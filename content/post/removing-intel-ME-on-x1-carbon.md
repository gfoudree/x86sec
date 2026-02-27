---
title: "Removing Intel Management Engine From Lenovo X1 Carbon 6th Gen Laptop"
date: 2022-09-08T00:00:00-00:00
draft: false
tags: [me_cleaner, lenovo x1 carbon, 6th gen, intel me, bios]
categories: []
summary: ""
---
## Intel Management Engine (ME) Removal 


## Getting existing firmware

The ME firmware is bundled as part of the UEFI firmware on a computer, so we must obtain a copy of the existing UEFI firmware first. It might be possible to download a BIOS bundle from Lenovo's website, but to ensure success I decided to just read it directly from the BIOS chip on my laptop.

There are several ways to read the BIOS chip, I chose to use an inexpensive ($13) [CH341A USB programmer](https://web.archive.org/web/20220908183748/https://www.amazon.com/KeeYees-SOIC8-EEPROM-CH341A-Programmer/dp/B07SHSL9X9) which comes with a nice 8-pin SOIC clip so nothing has to be desoldered. You can use anything that will run SPI commands (Buspirate, RPI, etc...).

Next we have to locate the BIOS chip on the motherboard. Typically, it is an 8-pin chip made by "Winbond" and if you lookup the part number it will be an SPI flash chip. On the X1 Carbon 6th gen, it is located under a sticker and the part number is `W25Q128JV`. From the datasheet we can see it is a 3.3V, 128M-Bit SPI Serial Flash chip. (The BIOS programmer does not list it as supported, but it works fine).


![bioschiplocation](/bios_chip_location.jpeg "BIOS chip location")

![winbondchip](/winbond_chip.webp "Windbond Chip")

Attach the SOIC clip with the RED cable oriented in the corner of the chip that has the circle on it then attach the header into the top part of the ZIF socket (25 BIOS section) and align it as such:

![programmerchip](/progrmamer_chip.jpeg "Programmer chip")

At this point, you should be able to read from the chip. We want to make a backup so we can restore the old BIOS if we break anything (and we will `:)`). If `flashrom` gives you an error, try fiddling with the clip and making sure it is attached properly.

```bash
└─$ flashrom --programmer ch341a_spi -r backup.bin    
flashrom v1.2 on Linux 5.4.0-125-generic (x86_64)
flashrom is free software, get the source code at https://flashrom.org

Using clock_gettime for delay loops (clk_id: 1, resolution: 1ns).
Found Winbond flash chip "W25Q128.V" (16384 kB, SPI) on ch341a_spi.
Reading flash... done.
```

**To be _extra_ safe, run the above command a couple more times to make extra backups and then verify the checksum (SHA512) is the _same_ across all of them. Sometimes a bad read might occur because the clip unseats, etc... and the last thing you want is a corrupted backup image.**

## Using me_cleaner

Download [me_cleaner](https://github.com/corna/me_cleaner) which we will use to disable/remove the Intel ME from the extracted firmware.

There's two main modes you can run `me_cleaner` with - remove as many ME components as possible, or set the HAP bit and ask ME to disable itself. We will start by trying the first option and removing most of the ME code.

```bash
└─$ python3 me_cleaner.py -S -O cleaned.bin ../../backup.bin                                                                                              
Full image detected
Found FPT header at 0x3010
Found 13 partition(s)
Found FTPR header: FTPR partition spans from 0x1000 to 0x130000
Found FTPR manifest at 0x1478
ME/TXE firmware version 11.8.92.4222 (generation 3)
Public key match: Intel ME, firmware versions 11.x.x.x
The HAP bit is NOT SET
Reading partitions list...
 FTPR (0x00001000 - 0x000130000, 0x0012f000 total bytes): NOT removed
 FTUP (0x00272000 - 0x000600000, 0x0038e000 total bytes): removed
 DLMP (0x0012e000 - 0x000131000, 0x00003000 total bytes): removed
 PSVN (0x00000e00 - 0x000001000, 0x00000200 total bytes): removed
 IVBP (0x0026e000 - 0x000272000, 0x00004000 total bytes): removed
 MFS  (0x00130000 - 0x00026e000, 0x0013e000 total bytes): removed
 NFTP (0x00272000 - 0x00057d000, 0x0030b000 total bytes): removed
 ROMB (      no data here      , 0x00000000 total bytes): nothing to remove
 WCOD (0x0057d000 - 0x0005fd000, 0x00080000 total bytes): removed
 LOCL (0x005fd000 - 0x000600000, 0x00003000 total bytes): removed
 FLOG (0x00600000 - 0x000601000, 0x00001000 total bytes): removed
 UTOK (0x00601000 - 0x000603000, 0x00002000 total bytes): removed
 ISHC (      no data here      , 0x00000000 total bytes): nothing to remove
Removing partition entries in FPT...
Removing EFFS presence flag...
Correcting checksum (0x98)...
Reading FTPR modules list...
 FTPR.man     (uncompressed, 0x001478 - 0x0021b4): NOT removed, partition manif.
 rbe.met      (uncompressed, 0x0021b4 - 0x00224a): NOT removed, module metadata
 fptemp.met   (uncompressed, 0x00224a - 0x002282): NOT removed, module metadata
 kernel.met   (uncompressed, 0x002282 - 0x002310): NOT removed, module metadata
 syslib.met   (uncompressed, 0x002310 - 0x002374): NOT removed, module metadata
 bup.met      (uncompressed, 0x002374 - 0x002936): NOT removed, module metadata
 pm.met       (uncompressed, 0x002936 - 0x0029e4): NOT removed, module metadata
 vfs.met      (uncompressed, 0x0029e4 - 0x003448): NOT removed, module metadata
 evtdisp.met  (uncompressed, 0x003448 - 0x0035d6): NOT removed, module metadata
 loadmgr.met  (uncompressed, 0x0035d6 - 0x0036fe): NOT removed, module metadata
 busdrv.met   (uncompressed, 0x0036fe - 0x003aa6): NOT removed, module metadata
 gpio.met     (uncompressed, 0x003aa6 - 0x003bf0): NOT removed, module metadata
 prtc.met     (uncompressed, 0x003bf0 - 0x003da0): NOT removed, module metadata
 policy.met   (uncompressed, 0x003da0 - 0x003f60): NOT removed, module metadata
 crypto.met   (uncompressed, 0x003f60 - 0x0040ea): NOT removed, module metadata
 heci.met     (uncompressed, 0x0040ea - 0x0042b6): NOT removed, module metadata
 storage.met  (uncompressed, 0x0042b6 - 0x0045b2): NOT removed, module metadata
 pmdrv.met    (uncompressed, 0x0045b2 - 0x0046d6): NOT removed, module metadata
 maestro.met  (uncompressed, 0x0046d6 - 0x0047c0): NOT removed, module metadata
 fpf.met      (uncompressed, 0x0047c0 - 0x0048d8): NOT removed, module metadata
 hci.met      (uncompressed, 0x0048d8 - 0x0049da): NOT removed, module metadata
 fwupdate.met (uncompressed, 0x0049da - 0x004ae2): NOT removed, module metadata
 ptt.met      (uncompressed, 0x004ae2 - 0x004bee): NOT removed, module metadata
 touch_fw.met (uncompressed, 0x004bee - 0x004d00): NOT removed, module metadata
 rbe          (Huffman     , 0x004d00 - 0x007bc0): NOT removed, essential
 fptemp       (LZMA/uncomp., 0x007bc0 - 0x009bc0): removed
 kernel       (Huffman     , 0x009bc0 - 0x019c00): NOT removed, essential
 syslib       (Huffman     , 0x019c00 - 0x02afc0): NOT removed, essential
 bup          (Huffman     , 0x02afc0 - 0x056040): NOT removed, essential
 pm           (Huffman     , 0x056040 - 0x059480): removed
 vfs          (Huffman     , 0x059480 - 0x067000): removed
 evtdisp      (Huffman     , 0x067000 - 0x069940): removed
 loadmgr      (Huffman     , 0x069940 - 0x06e740): removed
 busdrv       (Huffman     , 0x06e740 - 0x0721c0): removed
 gpio         (Huffman     , 0x0721c0 - 0x073e80): removed
 prtc         (Huffman     , 0x073e80 - 0x075000): removed
 policy       (Huffman     , 0x075000 - 0x0801c0): removed
 crypto       (Huffman     , 0x0801c0 - 0x09afc0): removed
 heci         (LZMA/uncomp., 0x09afc0 - 0x09ee80): removed
 storage      (Huffman     , 0x09ee80 - 0x0a4f00): removed
 pmdrv        (Huffman     , 0x0a4f00 - 0x0a6a80): removed
 maestro      (Huffman     , 0x0a6a80 - 0x0ab700): removed
 fpf          (Huffman     , 0x0ab700 - 0x0ae080): removed
 hci          (LZMA/uncomp., 0x0ae080 - 0x0ae900): removed
 fwupdate     (LZMA/uncomp., 0x0ae900 - 0x0b3640): removed
 ptt          (LZMA/uncomp., 0x0b3640 - 0x0c8fc0): removed
 touch_fw     (LZMA/uncomp., 0x0c8fc0 - 0x130000): removed
The ME minimum size should be 372736 bytes (0x5b000 bytes)
The ME region can be reduced up to:
 00003000:0005dfff me
Setting the HAP bit in PCHSTRP0 to disable Intel ME...
Checking the FTPR RSA signature... VALID
Done! Good luck!
```

It looks like it succeeded, great! Now let's flash the modified BIOS firmware back to the BIOS chip.

```bash
└─$ flashrom --programmer ch341a_spi -w Downloads/me_cleaner/cleaned.bin                                                                                
flashrom v1.2 on Linux 5.4.0-125-generic (x86_64)
flashrom is free software, get the source code at https://flashrom.org

Using clock_gettime for delay loops (clk_id: 1, resolution: 1ns).
Found Winbond flash chip "W25Q128.V" (16384 kB, SPI) on ch341a_spi.
Reading old flash chip contents... done.
Erasing and writing flash chip... Erase/write done.
Verifying flash... 
VERIFIED.
```

Now, let's disconnect the clip and power on the laptop... And we get a bunch of musical tones playing and a black screen. Great. It looks like this has removed some component that will not allow the laptop to boot. Restoring the backup firmware works fine and the laptop powers on without issues. Time for plan B...


## Setting the HAP bit

There is an undocumented setting (supposedly there for US Govermental agencies to use on sensitive devices) called the "High Assurance Platform" bit which tells the ME to disable itself. `me_cleaner` can be used to set this in our BIOS firmware - let's go ahead and give it a try:



```bash
└─$ python3 me_cleaner.py -s -O cleaned_soft.bin ../../backup.bin

Full image detected
Found FPT header at 0x3010
Found 13 partition(s)
Found FTPR header: FTPR partition spans from 0x1000 to 0x130000
Found FTPR manifest at 0x1478
ME/TXE firmware version 11.8.92.4222 (generation 3)
Public key match: Intel ME, firmware versions 11.x.x.x
The HAP bit is NOT SET
Setting the HAP bit in PCHSTRP0 to disable Intel ME...
Checking the FTPR RSA signature... VALID
Done! Good luck!
```

Flashing this version back to the board works great and the laptop powers right up without any issues!

## Checking if the ME has been disabled/removed

There are several ways we can try and check if the ME has been disabled. [MEI AMT Check](https://github.com/mjg59/mei-amt-check) will tell us if AMT is working (part of the ME) and running it appears like it is disabled. So far so good :)


```bash
└─$ sudo ./mei-amt-check
Unable to find a Management Engine interface - run sudo modprobe mei_me and retry.
If you receive the same error, this system does not have AMT
```

Next, let's try [Coreboot's tool to check](https://github.com/corna/me_cleaner/wiki/Get-the-status-of-Intel-ME). There's an error at the top (but some forums say to ignore it) and it too reports it can't find the PCI device presented by the ME.


```bash
└─$ sudo ./intelmetool -d -m                                                                                        
Bad news, you have a `Sunrise Point LPC Controller/eSPI Controller` so you have ME hardware on board and you can't control or disable it, continuing...

ME PCI device is hidden
RCBA addr: 0x00000000
Can't find ME PCI device
```

Intel also has a ME version checker tool which also reports an issue talking to the ME.

```bash
└─$ sudo ./intel_csme_version_detection_tool --help                                                                                       
Intel(R) CSME Version Detection Tool
Copyright(C) 2017-2022, Intel Corporation, All rights reserved.

Application Version: 7.0.2.0
Scan date: 2022-09-08 05:14:21 GMT

*** Host Computer Information ***
Name: dell-pc
Manufacturer: LENOVO
Model: 20KGS3XR00
Processor Name: Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz
OS Version: Manjaro Linux (5.15.60-1-MANJARO)

*** Risk Assessment ***
  Detection Error: This system may be vulnerable,
  either the Intel(R) MEI/TXEI driver is not installed
  (available from your system manufacturer)
  or the system manufacturer does not permit access
  to the ME/TXE from the host driver.
```

Finally, let's see if the BIOS configuration page has any details:

![biossettings](/bios_settings.jpeg)

We can see that no version of the ME is detected! All 4 separate methods all report the ME as inaccessible/disabled which leads me to believe setting the HAP bit was successful in disabling it.