---
layout: post
title: "Simple ELF Crypter"
author: "Grant"
tags: [elf, binary, binary crypter, malware, elf crypter]
---

# ELF Files
<hr>
There are several techniques that can be used to obsfucate what an executable does at runtime. This post will demonstrate a minimal example of a self-modifying, ELF executable that contains an encrypted section of code that, at runtime, bruteforces its own key and decrypts itself.

## ELF Sections

ELF executables are comprised of several "sections". Code that is executed, such as `int main()`, is placed inside the `.text` section.
```bash
> readelf -S a.out 
There are 30 section headers, starting at offset 0x29d8:

Section Headers:
  [Nr] Name              Type             Address           Offset
       Size              EntSize          Flags  Link  Info  Align
  [ 0]                   NULL             0000000000000000  00000000
       0000000000000000  0000000000000000           0     0     0
  [ 1] .interp           PROGBITS         0000000000400238  00000238
       000000000000001c  0000000000000000   A       0     0     1
  ...
  [13] .text             PROGBITS         0000000000400490  00000490
       00000000000002b2  0000000000000000  AX       0     0     16
```

To make things easier for our encryption tool, we will create a new section called `.elf` where we will put the functions and strings we want to protect. In GCC, thankfully this is as simple as tagging a function with the section attribute: `__attribute__((section(".elf")))`.

## Code Layout

In our program, we are going to protect the function `main()` so we will "sandwich" it with two functions to mark the start and end so we have pointers to the region we will be decrypting at runtime.

```c
#define CRYPT_SECTION ".elf"

// Align 4k so memprotect works on page aligned data
void section_start() __attribute__((section(CRYPT_SECTION)))
    __attribute__((aligned(4096)));
// Protected (encrypted) function
int main() __attribute__((section(CRYPT_SECTION)));
// Mark end
void sentinal() __attribute__((section(CRYPT_SECTION))); 
```

We will define the body of `section_start()` as 4 NOPs and compile with `-fomit-frame-pointer`. This will help us to bruteforce the key as the decryption routine will attempt to guess the key until the signature of `\x90\x90\x90\x90` (4 NOPs) is found, revealing the guess is correct.

```c
void section_start() {                                                     
    __asm__ volatile("nop\n\tnop\n\tnop\n\tnop\n\t");
}
```

Our `main()` function can contain whatever we want. It is noteworthy to point out that any constant strings placed in here will likely **not** be encrypted unless we use a couple tricks. This is because the compiler will take the read-only string and place it in the `.rodata` section of the ELF (not the `.elf` section we want so that it is encrypted). To circumvent this, we will hack in a string by dynamically computing it as shown below.

```c
int main() { // Encrypted main function
    char buf[3];
    buf[0] = 'H'; // Build string
    buf[1] = 'i';
    buf[2] = '\0';
    printf("%s\n", buf);
    exit(0); // Call exit for clean exit
}

```

## Decryption Routine

When the encrypted program executes, it will need to bruteforce the decryption key so it can decrypt the protected region and jump to it. To accomplish all of this, the protected region needs to have the memory permissions of RWX so we will set it with `mprotect(void *addr, size_t len, int prot)`. With few exceptions, process memory regions are set to not allow writing and execution at the same time (W^X) for security reasons. Because of this, we have to call `mprotect`. 
<br>
<br>
To calculate the starting address and length of the encrypted region we need to pass to `mprotect`, we can do some simple pointer math:

```c
unsigned int len = (&sentinal) - (&section_start);
mprotect(&section_start, len, PROT_READ|PROT_WRITE|PROT_EXEC);
```

Now that the memory can be modified, let's iterate over it and attempt to bruteforce the key by checking if our guess decrypts the first 4 bytes of `section_start()` to be `\0x90\0x90\0x90\0x90`:

```c
// Pointer to start of encrypted .elf section & our helper function of NOPs
unsigned char *ptr = (unsigned char *)&section_start;
unsigned int key = 0;

for (unsigned int i = 0; i < 0xFFFFFFFF; i++) { // Bruteforce 32-bit key
    // Check for our 4 NOP opcodes
    if (((*(ptr) ^ i) == 0x90) && ((*(ptr + 1) ^ i) == 0x90) &&
         ((*(ptr + 2) ^ i) == 0x90) && ((*(ptr + 3) ^ i) == 0x90)) {
        key = i;
        break;
    }
}
printf("Found the key! %d\n", key);
```

Now that the decryption key is found, we just have to decrypt the region and then jump to it:
```c
for (int i = 0; i < len; i++) {
    unsigned char v = *(ptr + i);
    *(ptr + i) = v ^ key; // Do decryption
}
main(); // Call decrypted function!
```

## Encrypting The ELF File

Since the content we are encrypting is located in the `.elf` section we created above, we need a simple program to locate the section boundries of `.elf` and encrypt it.
<br>
<br>
[Pwntools](https://docs.pwntools.com/en/stable/) is a great Python library for doing CTFs, pentesting, and shellcoding. We will use their ELF library to make things easier.

```python
#!/usr/bin/python2
from pwn import *
import os

def encryptSection(e):
	cryptSection = e.get_section_by_name('.elf')
	baseAddr = cryptSection['sh_offset']
	sz = cryptSection['sh_size']

	print("Entry point @ 0x{:02X}".format(e.address))
	print("Crypted Section @ 0x{:02X} - 0x{:02X} Size: {}B".format(baseAddr, baseAddr + sz, sz))

	secData = e.read(e.address + baseAddr, sz)

        # Encrypt data with XOR cipher (Key = 0xE3)
	encryptedData = [chr((ord(x)^0xe3)) for x in list(secData)]

	print(hexdump(secData))
	print("Encrypted:")
	print(hexdump(encryptedData))

	e.write(e.address + baseAddr, ''.join(encryptedData))

e = ELF("./a.out")
encryptSection(e)
e.save("encrypted.elf")
os.chmod("encrypted.elf", 0777)
```

Inspecting the the first 5 instructions of the to-be-protected `main()` function before encrypting it gives us the following disassembly:

```bash
[0x004005c7]> pd 5 @ sym.main
           0x00401006      4883ec28       sub rsp, 0x28
           0x0040100a      64488b042528.  mov rax, qword fs:[0x28]
           0x00401013      4889442418     mov qword [var_10h], rax
           0x00401018      31c0           xor eax, eax
           0x0040101a      c6042449       mov byte [rsp], 0x49
```

Disassembling the same function in the encrypted ELF file gives us:
```bash
[0x004005c7]> pd 5 @ sym.main
           0x00401006      ab             stosd dword [rdi], eax
           0x00401007      60             invalid
           0x00401008      0fcb           bswap ebx
           0x0040100a      87ab68e7c6cb   xchg dword [rbx - 0x34391898], ebp
           0x00401010      e3e3           jrcxz 0x400ff5
```

As you can see, the opcodes have changed as expected. The first opcode `0x48` XORed with our key `0xe3`, gives us the result `0xab` we are seeing in the encrypted binary. 
<br>
<br>
By encrypting the region, the opcodes are no longer valid and the disassembler cannot determine what this region of code does. Worse, opcodes will be generated that decode to jump instructions which will result in incorrect control-flow graphs of the code.

# Testing & Code
<hr>

## Source Code

Download: [simple_elf_crypter.tar.gz](/assets/simple_elf_crypter.tar.gz)
# Demo Environment
<hr>
I created a Docker Container where you can play around with the source and compiled code. If you want to see how the decryption works during runtime, launch the docker container and run the `encrypted.elf` in GDB.

```bash
docker run -ti gfoudree/simple-elf-crypter:latest
```

Then run `make` inside the container to build `a.out` (the executable before being encrypted) and `encrypted.elf` (encrypted executable).