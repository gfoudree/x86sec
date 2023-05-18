---
layout: post
title: "Sierra Wireless EM7455 4G Modem Hacking"
author: "Grant"
tags: [4g, lte, modem, crack, em7455, reverseengineer, firmware]
---

# Sierra Wireless EM7455, 4G Modem
<hr>
Modems are in many devices, perhaps most importantly your cellphone. These devices are almost exclusively black boxes and run lots of code the end-user has zero knowledge or access to. Additionally, these modems interface with the host via USB and sometimes PCI which gives them the potential to access privileged information on the host.


![EM7455](/assets/em7455.jpeg){:width="30%" height="80%"}
# Changing IMEI
**WARNING** - It appears as if you can only change the IMEI *ONCE*. I did not try doing any serious resetting of the modem, but issuing multiple commands to set the IMEI fails so beware.

The IMEI on a cellular device uniquely identifies it and is used to block/accept and even track devices. Here we will see how to change it on the em7455 modem. Let's start by checking the current IMEI with ModemManager (I've changed mine for privacy reasons):

```bash
└─$ mmcli -m 0 | grep 3GPP

  3GPP     |                   imei: 352819381928531
```

To change the IMEI, we need to unlock level 3 engineering commands with the `AT!OPENLOCK?` command. The command will generate a random challenge, to which a response must be computed and sent to authenticate. Luckily, someone has reverse engineered this algorithm and we can use a script to generate the response :) [https://github.com/bkerler/edl/blob/master/sierrakeygen_README.md](https://github.com/bkerler/edl/blob/master/sierrakeygen_README.md)

```
AT!OPENLOCK?
39D0447ED86B4619
```

Here we see the challenge is `39D0447ED86B4619, so we will use the script to generate the response:

```bash
└─$ ./sierrakeygen -l 39D0447ED86B4619 -d MDM9x30
AT!OPENLOCK="994673746F1FDCA6"
```

The reponse is `994673746F1FDCA6`. The `MDM9x30` specifies the type of modem we have (em7455). Let's send this back as an AT command now:
```
AT!OPENLOCK="994673746F1FDCA6"
OK
```

Nice! Now we will unlock the ability to write a new IMEI and then set the new IMEI to what we would like it to be. The format is 8 bytes, comma-separated as shown below. We will change one byte `28->29`

![Write IMEI](/assets/write_imei.webp)

```
AT!NVIMEIUNLOCK
OK
AT!NVENCRYPTIMEI=35,28,19,38,19,29,53,10
OK
AT!RESET
```

Check the new IMEI
```bash
└─$ mmcli -m 0 | grep 3GPP

  3GPP     |                   imei: 352819381929531
```

# Firmware

## Structure
Sierra Wireless posts their firmware here [https://source.sierrawireless.com/resources/airprime/minicard/74xx/em_mc74xx-approved-fw-packages/](https://source.sierrawireless.com/resources/airprime/minicard/74xx/em_mc74xx-approved-fw-packages/). Inside the zip files are two items, a `.CWE` file with the modem firmware and a `.PRI` file with carrier information.

Binwalk gives us a lot of information - it appears as if there's an Android image and Linux image (possibly the same) inside

```bash
└─$ binwalk SWI9X30C_02.38.00.00.cwe 

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
1200          0x4B0           Qualcomm SBL1, image addr: ffffffff, image size: 4294967295, code size: 4294967295, sig size: 4294967295, cert chain size: 4294967295, oem_root_cert_sel: 4294967295, oem_num_root_certs: 4294967295
3248          0xCB0           Qualcomm SBL1, image addr: ffffffff, image size: 4294967295, code size: 4294967295, sig size: 4294967295, cert chain size: 4294967295, oem_root_cert_sel: 4294967295, oem_num_root_certs: 4294967295
5296          0x14B0          Qualcomm SBL1, image addr: ffffffff, image size: 4294967295, code size: 4294967295, sig size: 4294967295, cert chain size: 4294967295, oem_root_cert_sel: 4294967295, oem_num_root_certs: 4294967295
7344          0x1CB0          Qualcomm SBL1, image addr: ffffffff, image size: 4294967295, code size: 4294967295, sig size: 4294967295, cert chain size: 4294967295, oem_root_cert_sel: 4294967295, oem_num_root_certs: 4294967295
11440         0x2CB0          Qualcomm SBL1, image addr: f8004000, image size: 185124, code size: 185124, sig size: 0, cert chain size: 0, oem_root_cert_sel: 1, oem_num_root_certs: 1
29516         0x734C          Ubiquiti partition header, header size: 56 bytes, name: "PARTNUM_SHFT", base address: 0x08A16B46, data size: -168230248 bytes
87968         0x157A0         Unix path: /dev/icbcfg/boot
130004        0x1FBD4         Unix path: /dev/icbcfg/boot
132272        0x204B0         Qualcomm SBL1, image addr: 4798a002, image size: 3172001790, code size: 4160937384, sig size: 1852793695, cert chain size: 99, oem_root_cert_sel: 3182884850, oem_num_root_certs: 2962273648
143468        0x2306C         Qualcomm SBL1, image addr: 0, image size: 0, code size: 0, sig size: 4232054344, cert chain size: 4232054472, oem_root_cert_sel: 4232054624, oem_num_root_certs: 4232054600
171572        0x29E34         CRC32 polynomial table, little endian
175820        0x2AECC         CRC32 polynomial table, little endian
243152        0x3B5D0         ATAGs msm parition table (msmptbl), version: 55EE73AA,
245628        0x3BF7C         ATAGs msm parition table (msmptbl), version: 55EE73AA,
344016        0x53FD0         ELF, 32-bit LSB executable, ARM, version 1 (SYSV)
619808        0x97520         XML document, version: "1.0"
619880        0x97568         SHA256 hash constants, little endian
635796        0x9B394         mcrypt 2.5 encrypted data, algorithm: "-", keysize: 4608 bytes, mode: " ",
700184        0xAAF18         ELF, 32-bit LSB executable, ARM, version 1 (SYSV)
822348        0xC8C4C         Unix path: /dev/icb/rpm
852976        0xD03F0         Unix path: /dev/icb/rpm
853700        0xD06C4         Zlib compressed data, default compression
32256076      0x1EC304C       CRC32 polynomial table, little endian
32270648      0x1EC6938       Android bootimg, kernel size: 0 bytes, kernel addr: 0x66696E55, ramdisk size: 543450473 bytes, ramdisk addr: 0x746F6F62, product name: "ot partition found"
32273056      0x1EC72A0       Qualcomm splash screen, width: 0, height: 1634496627, type: 26739, blocks: 1330795077
32281396      0x1EC9334       Certificate in DER format (x509 v3), header length: 4, sequence length: 1187
32282587      0x1EC97DB       Certificate in DER format (x509 v3), header length: 4, sequence length: 1031
32283622      0x1EC9BE6       Certificate in DER format (x509 v3), header length: 4, sequence length: 1049
32287940      0x1ECACC4       Zlib compressed data, default compression
42761960      0x28C7EE8       Zlib compressed data, default compression
59125932      0x38630AC       Zlib compressed data, default compression
```

We can extract out the images with `binwalk -e`, giving us 4 chunks of compressed data. Inspecting them with binwalk again, we can see that 3 of them are YAFFS filesystems and 1 is an Android image

```bash
└─$ binwalk 1ECACC4

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             YAFFS filesystem, little endian
55328         0xD820          HTML document header
55365         0xD845          HTML document footer
157472        0x26720         Executable script, shebang: "/bin/sh"

└─$ binwalk 38630AC

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             Android bootimg, kernel size: 5068304 bytes, kernel addr: 0x7108000, ramdisk size: 0 bytes, ramdisk addr: 0x7108000, product name: ""
4096          0x1000          Linux kernel ARM boot executable zImage (little-endian)
```


## Contents
We can use `unyaffs` to extract these 3 filesystems to disk so we can inspect them. Looking in the first image, there appears to be a webserver running with static pages:

```bash
┌──(gfoudree㉿dell-pc)-[~/…/_SWI9X30C_02.38.00.00.cwe.extracted/fs/WEBSERVER/www]
└─$ ls
cgi-bin                  QCMAP_Account.html        QCMAP.html            QCMAP_IPV6.html      QCMAP_UPNP_DLNA_MDNS_Help.html  QCMAP_WWAN_Help.html
images                   QCMAP_Firewall_Help.html  QCMAP_IPV4_Help.html  QCMAP_login.html     QCMAP_UPNP_DLNA_MDNS.html       QCMAP_WWAN.html
js                       QCMAP_Firewall.html       QCMAP_IPV4.html       QCMAP_NAT_Help.html  QCMAP_WLAN_Help.html
QCMAP_Account_Help.html  QCMAP_Help.html           QCMAP_IPV6_Help.html  QCMAP_NAT.html       QCMAP_WLAN.html
```

Looking at some of these files, it appears to be some management web UI for the modem to configure IP/FW/WLAN settings. There's also CGI files which seem to run the backend.

![Firmware webui](/assets/firmware_webui.webp)


### Web UI Password

Opening `cgi-bin/qcmap_auth` in Ghidra, it appears to be a simple binary that performs authentication of the "admin" account. It does so by opening a file `/www/lighttpd.user` which contains the password for the user with a hash and salt. The contents of the file are:

```
admin:$6$28780376880137ae$sy2ToGy3NjYEPTfOPZT7/IMEr0MN9F6gZbrt6e0881usmBPFGAKy1sYGNNz6GMcfqcx2aRJn95qm/551AIqNk/
```

In Ghidra, there is a function at `0x00008c40` which performs this authentication. First, the `/www/lighttpd.user` is opened, then `fseek(6)` is used to skip past the `admin:` portion and to the hash section where `fread(0x6b)` is called to read this.

![Auth](/assets/modem_auth_mechanism.webp)

To perform the hash, the binary uses the `crypt()` function

![hash](/assets/modem_hash_func.webp)

Now that we know the hashing algorithm that is being used, we can crack the password. Let's try something obvious with Python - the credentials admin/admin

```python
import crypt
crypt.crypt('admin', '$6$28780376880137ae')
```
```
$6$28780376880137ae$sy2ToGy3NjYEPTfOPZT7/IMEr0MN9F6gZbrt6e0881usmBPFGAKy1sYGNNz6GMcfqcx2aRJn95qm/551AIqNk/
```
...It's the same of the contents of `/www/lighttpd.user`. Success! 

Finally, there is one more password on the YAFFS image in `/etc/shadow`:
```
└─$ cat fs/etc/shadow 
root:C98ULvDZe7zQ2:19005:0:99999:7:::
```

A quick Google shows the password is `oelinux123`.

Sadly, I'm unable to boot up the webserver researched above, or even an ADB port on the em7455 to check the passwords unfortunately.

### Extracting AT Commands
Inside the 3rd image there a bunch of modem files

```bash
┌──(gfoudree㉿dell-pc)-[~/Downloads/_SWI9X30C_02.38.00.00.cwe.extracted/fs3/image]
└─$ ls
adsp.b00  adsp.b03  adsp.b06  bdwlan20.bin            mba.mdt    modem.b02  modem.b05  modem.b08  modem.b11  modem.b16  modem.b20  qwlan20.bin
adsp.b01  adsp.b04  adsp.b07  extract_at_commands.py  modem.b00  modem.b03  modem.b06  modem.b09  modem.b12  modem.b17  modem.mdt  utf20.bin
adsp.b02  adsp.b05  adsp.mdt  mba.b00                 modem.b01  modem.b04  modem.b07  modem.b10  modem.b13  modem.b18  otp20.bin  Ver_Info.txt
```

Running `strings` on the `modem.b12` file I noticed there were lots of `AT` commands. Usually devices like this publish a set of public commands, but contain some hidden commands. Hopefully we can discover some undocumented ones and poke around the modem. With a simple Python script we can extract the `AT` commands.


```python
import re

d = open('modem.b12', 'rb').read()
for m in re.findall(b'\x00+([!+$>^][A-Z]+)\x00+', d):
    print(m.decode())
```
The list is too long, so I am posting them all here: [AT_commands.txt](/assets/AT_commands.txt)

I tried many of the AT commands only to find out lots of them were unimplemented or returned "error". My guess is this firmware is used across many different hardware versions with some of them implementing the commands. That or I am unable to find a way to "unlock" these command. Sadly I did not find anything interesting here, but perhaps with more digging I might.