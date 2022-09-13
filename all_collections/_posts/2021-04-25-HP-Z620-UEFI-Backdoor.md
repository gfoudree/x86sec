---
layout: post
title: "HP z620 UEFI Backdoor"
author: "Grant"
tags: [z620, reverse engineering, uefi, backdoor, malware, persistent, ghidra, efi]
---

# Firmware Analysis
<hr>

Picking apart firmware is quite interesting to me and so I thought it would be fun to reverse engineer my desktop's BIOS and see what I could find.

## Extracting UEFI Modules

My desktop is an HP z620 and the latest BIOS version is [J61_0396.bin](/assets/J61_0396.bin). Most UEFI BIOS images are a collection of modules (drivers, microcode, applications, etc...) that can be extracted and examined. The drivers and applications are PE32+ executables which is convenient as many reverse engineering tools support this executable format. We can examine/modify the BIOS image with [UEFITool](https://github.com/LongSoft/UEFITool) and pick apart the sections of interest.

An easy section to look at is where the POST logo is stored. Here it's conveniently called "Logo" and we can extract it as a `.bmp` file and see it is the same logo shown during POST.

![Placeholder image](/assets/bios_logo.png "UEFITool bios logo section") ![Placeholder image](/assets/hp_bios_logo.png "HP BIOS logo")
<br>

Sifting through the remaining sections, `BiosDiags` and `AbsoluteDriver` stood out as interesting as they are both applications.
<br>
<br>

![Placeholder image](/assets/uefi_biosdiags_efi.png "UEFITool BiosDiags.efi")
<br>

## Reverse Engineering BiosDiags.efi

After extracting the `BiosDiags` section (Right-click "PE32 Image Section" -> "Extract Body"), let's open it up in Ghidra to have a look...

**Note:** to help with analyzing BIOS images, the plugins [ghidra-firmware-utils](https://github.com/al3xtjames/ghidra-firmware-utils) and [efiSeek](https://github.com/DSecurity/efiSeek) are helpful.


Looking for strings, `rpcnetp.exe` shows up inside shortly followed by the familiar `MZ` header which indicates a PE executable file. Interesting... The suspected PE executable is in the `.data` section of `BiosDiags.efi` which further raises suspicion that this is an embedded program to be dumped somewhere and not executed as part of `BiosDiags.efi`.

![Placeholder image](/assets/embedded_pe_header.png "embedded PE header")


## Running BiosDiags.efi

Let's confirm our suspicions and run `BiosDiags.efi` in QEMU with an attached disk with Windows XP installed to see what happens.

An easy way to run EFI programs is launch QEMU with a UEFI BIOS, get a UEFI shell and invoke the program from there. Download a UEFI shell (or use [this one](/assets/Shell.efi)) and build an EFI-bootable FAT32 disk.


```bash
dd if=/dev/zero of=disk.img bs=1M count=64
mkfs.msdos disk.img
mmd -i disk.img ::/EFI
mmd -i disk.img ::/EFI/BOOT

## Copy in shell & BiosDiags.efi
mcopy -i disk.img Shell.efi ::/EFI/BOOT/Bootx64.efi
mcopy -i disk.img BiosDiags.efi ::/
```

Invoke QEMU and attach a disk image with Windows XP installed (you can install the OVMF UEFI firmware on Ubuntu with `apt install ovmf`)
```bash
qemu-system-x86_64 -drive format=raw,file=disk.img \
    -smp 2 -m 4096 -bios /usr/share/qemu/OVMF.fd \
    -drive media=disk,file=WindowsXP_1.vmdk 
```

Once QEMU starts up, you can drop into a shell and invoke `BiosDiags.efi`

```bash
FS0:
BiosDiags.efi
```

![qemubiosdiags](/assets/qemu_biosdiags_efi.png "running BiosDiags.efi in QEMU")

Booting up XP we can see that two new files are implanted in `C:\Windows\System32\` as suspected (`rpcnetp.exe` and `rpcnetp.dll`) and `rpcnetp.exe` is running as `SYSTEM` on the machine. Nice!

![xpbackdoor](/assets/backdoor_running.png "backdoor running")

It is worth noting that trying this again on a Windows 7 machine does not produce the same results, and no `rpcnet.exe` is dropped.

## WPBT (Windows Platform Binary Table)

This sort of behavior looks a lot like a bootkit but, to my surprise, Windows provides an official way to do this via the [Windows Platform Binary Table](https://download.microsoft.com/download/8/A/2/8A2FB72D-9B96-4E2D-A559-4A27CF905A80/windows-platform-binary-table.docx) (WPBT). In essence, the WPBT allows UEFI firmware to register a PE file to be run during system initialization by inserting it into an ACPI table. The ACPI table format looks like this (see above link for full details):

![wpbtlayout](/assets/wpbt_layout.png "wpbt layout")

It appears as if this is exactly what is going on here. Let's have a look.

![acpitable](/assets/acpi_table_manipulation.png "acpi table manipulation")
<br>
In this function, `0x80005de0`, we can see it accessing some ACPI tables in the beginning.

In Microsoft's documentation for WPBT, UEFI firmware is supposed to allocate memory for the WPBT ACPI table via the `AllocatePages()` service with an allocation type of `AllocateAnyPages` and the `EfiACPIReclaimMemory` flag set. This is **exactly** what we see later on inside `0x80005de0` :).

<br>
![allocpages](/assets/acpi_alloc_pages.png "alloc pages")
<br>

Lines 64 & 65 perform this allocation, with line 68 invoking a function that takes in the PE code for the dropped `rpcnetp.exe` file. Finally, line 69 stores the result in `Table` which is our ACPI table that will be used to implement WPBT.

<br>
![wpbttable](/assets/wpbt_table.png "wpbt table")
<br>

Continuing on, we can see the WPBT fields being filled out per the specification. Line 111 sets the mandatory `WPBT` signature (`0x54425057` translates to "WPBT"). On line 119 we can see the `DAT_800010a8` value referenced again and set as the length of the PE data (`puVar14` is a 32-bit variable so `puVar14[9]` = 4*9 -> 36). The content flag is set to 1 (indicating a PE file) and finally the memory location is set to that allocated buffer the PE data was copied into above.

Skipping over some lines, we eventually come to the end of the function where we can see the new ACPI table being installed with `InstallConfigurationTable()` and it's GUID, exactly as outlined in Microsoft's documentation.
<br>

![installwpbt](/assets/install_wpbt.png "wpbt install")


## Dropped file analysis

Running both the files through Virustotal shows both files flagging 1 AV out of 67 ([rpcnetp.exe](https://www.virustotal.com/gui/file/1c6a20980a186225979f5e91bc48eaf77c67f50eea85eba9db4c3ec55c61d55f/detection) [rpcnetp.dll](https://www.virustotal.com/gui/file/56c9ab9a663af6af931b3c76f32ed0f7402d6ed39f3538f72cb2757886ef7c40/detection))

Digging further, it appears this program is called "Computrace" and has been around for a while. I suppose the string at the beginning of the EFI file should have alerted me to this as well...

![computrace](/assets/computrace.png "computrace")

If you're interested, you can read more about it here from this [Blackhat 14 Presentation](http://blackhat.com/docs/us-14/materials/us-14-Kamlyuk-Kamluk-Computrace-Backdoor-Revisited.pdf) which goes over what it does.


## Closing thoughts

While it appears as if Computrace does not deploy on newer Windows installations, it is important to realize this method of stealthily dropping executables into a OS install is a very real concept and is being used. Microsoft provides a way for vendors to do this so it is highly likely other software is being installed this way as well. Although other operating systems, like Linux, don't provide a built-in way to do this, accessing the disk in a pre-boot environment and dropping executables or modifying the guest OS is quite realistic. Since BIOS code is mostly black-box software that runs with high privilege before the OS boots, one should realize the trust we place in this firmware that we cannot control nor do we understand everything it does.

## Files

#### HP BIOS & EFI Modules
[`BiosDiags.efi`](/assets/BiosDiags.efi):`71b01f0ad7c1d990771aa675bc814d5f9b50a7958c005173cda0165139235666`
[`J61_0396.bin`](/assets/J61_0396.bin):`05e89382e73afb280f637acbfa1029e9107dd30c78df37b6a00f184657f5f2c3`

#### UEFI BIOS for QEMU
[`OVMF.fd`](/assets/OVMF.fd):`96a9aad279ac9fdb7d452b70cee71587a917aaa428e4c40e9a9cb35f5d718259`
[`Shell.efi`](/assets/Shell.efi):`04c89f19efee2a22660fd4650ff9add88e962d102b1b713e535f4e32a07c5185`

#### Computrace 
[`rpcnetp.dll`](/assets/rpcnetp.dll):`56c9ab9a663af6af931b3c76f32ed0f7402d6ed39f3538f72cb2757886ef7c40`
[`rpcnetp.exe`](/assets/rpcnetp.exe):`1c6a20980a186225979f5e91bc48eaf77c67f50eea85eba9db4c3ec55c61d55f`