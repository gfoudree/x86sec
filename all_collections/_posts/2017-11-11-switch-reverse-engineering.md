---
layout: post
title: "TEG-S18TXE Switch Reverse Engineering"
author: "Grant"
tags: [eeprom, reverse engineering, Trendnet, TEG-S18TXE, network switch, Arduino]
---

# TEG-S18TXE Switch
<hr>

I happened to have an old [Trendnet TEG-S18TXE switch](https://www.trendnet.com/products/proddetail?prod=185_TEG-S18TXE)
  laying around the lab at work, so I decided to open it up and see if there was
  anything interesting inside. Usually, "dumb" switches do not contain many interesting hackable components
  as they are rather simplistic devices, however I got lucky and spotted an EEPROM chip on the board. If you look closely,
  you might notice that it is an Atmel AT93C46, 1K serial EEPROM.

![Placeholder image](/assets/board1.png "Placeholder image")

Interestingly, there appear to be unpopulated headers right below the chip that are connected to some of the pins on the EEPROM.
  Instead of soldering on some pins to the headers, I decided to use a SOP16 Clip which allowed me to access the pins on the DIP chip quite nicely.

![Placeholder image](/assets/board2.png "Placeholder image")

Following the datasheet [here](http://www.atmel.com/Images/doc5140.pdf), I grabbed a spare Arduino Pro Micro and hooked up the wires as such:

![Placeholder image](/assets/chip1.png "Placeholder image")


| EEPROM | Arduino       |
|:------:|:-------------:|
| VCC    | VCC           |
| GND    | GND           |
| SK     | SCLK (Pin 15) |
| CS     | Pin 9         |
| DI     | MOSI (Pin 16) |
| DO     | MISO (Pin 14) |

<br>

With everything connected, the only thing left to do was write some code to dump the EEPROM.

```c
#include <SPI.h>
#define SS_PIN 9

void setup() {
  pinMode(SS_PIN, OUTPUT);
  digitalWrite(SS_PIN, LOW);

  Serial.begin(9600);

  SPI.begin();
  SPI.setClockDivider(SPI_CLOCK_DIV128);
  SPI.setDataMode(SPI_MODE0);
  SPI.setBitOrder(MSBFIRST);
}

void loop() {
  byte data, b1, b2;

  for (int i = 0; i < 128; i++) {
    digitalWrite(SS_PIN, HIGH);
    SPI.transfer(3);
    SPI.transfer(i); //Address to read
    delay(10);

    b1 = SPI.transfer(0);
    b2 = SPI.transfer(0);

    digitalWrite(SS_PIN, LOW);

    b1 = b1 << 1;
    b2 = b2 >> 7;
    data = b1 | b2;

    Serial.print(i, DEC);
    Serial.print(" = ");
    Serial.println(data, HEX);
    delay(50);
  }
}
```

  Success! Monitoring the serial console gives a dump of the entire chip, but it looks like only the first 0x23 bytes contain data - the rest are zeros.

```bash
$ xxd eeprom_dump.bin
00000000: 8daa 01ff 1a00 0112 0002 01ff 0000 0128  ...............(
00000010: ffff 01ff 0000 02fa 7800 68ea 01ff 3300  ........x.h...3.
00000020: 012a 0018   
```

  At this point it is pretty difficult to discern what each byte/bit corresponds to. I tried hooking up the switch to a couple computers and doing a large
  file transfer, as well as power-cycling the device several times in an attempt to expose some hints. However when I dumped the EEPROM after, nothing had changed.
  My best guess is that the unpopulated header on the board is used to program some simple configuration settings to the device during production and that is the extent
  to which the chip is written to. Since EEPROM has limited write cycles, combined with the fact that unmanaged switches don't really need to store persistant data, it
  is unlikely this EEPROM gets modified.