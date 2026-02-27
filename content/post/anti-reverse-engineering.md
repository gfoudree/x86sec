---
title: "Anti Reverse Engineering Tricks"
date: 2018-03-05T00:00:00-00:00
draft: false
tags: [reverse engineering, obsfucation]
categories: []
summary: ""
---
## Jumping Over Opcodes

<br>
It is not uncommon for malware to attempt to obfuscate its behavior in various ways to avoid analysis. In this post we will go over
some common tricks used to confuse static analysis tools from obtaining the correct disassembly of a program.

A very simple trick is to jump over instructions that we don't want to execute. Obviously this can get more complex, but the concept is simple.

```assembly
//Compile with gcc trick1.S
.text
.global main
main:
	jmp L1 + 1
L1:
	.byte 0xc3               //Disassembler interprets this as a "ret" when we are really jumping over this (jmp L1 + 1)
	movq $1, %rax

exit:
	mov $60, %rax
	xor %rdi, %rdi
	syscall                  //Call exit(1)
```

The disassembly of the binary is shown below (objdump)

```bash
0000000000400487 <main>:
  400487:	eb 01                	jmp    40048a <L1+0x1>

0000000000400489 <L1>:
  400489:	c3                   	ret                 //It appears as if we are returning here, but we never execute this opcode
  40048a:	48 c7 c0 01 00 00 00 	mov    rax,0x1      //We jump here

0000000000400491 <exit>:
  400491:	48 c7 c0 3c 00 00 00 	mov    rax,0x3c
  400498:	48 31 ff             	xor    rdi,rdi
  40049b:	0f 05                	syscall
  40049d:	0f 1f 00             	nop    DWORD PTR [rax]
```

Some disassemblers can be easily tricked by making the program appear as if it jumps into the middle of an opcode. This has a cascading effect
  of causing the disassembler to misinterpret most of the surrounding code, effectively obfuscating it.

## Invalid Opcodes

<br>
We will use a technique that combines the trick above with an alternative way to jump to code in order to confuse the disassembler.
  Recall that the "call" instruction pushes the address of the next instruction to the stack then jumps to the location.
  We can have fun with this by using it to get the current value of RIP, adding some value to it, pushing it to the stack and calling "ret"
  effectively making a dynamic "jmp" instruction. The disassembler, however, does not really know we are jumping somewhere as it never
  sees a "jmp" instruction.

```assembly
call L1+1		//0xe8, 0x01, 0x00, 0x00	[Push RIP of return addr to stack and jump to 'pop rax']
L1: .byte 0xe9          //0xe9 				[Dummy val to confuse disasm]
pop rax 		//0x58 				[RIP = addr of this instruction, rax = RIP]
add rax, 9		//0x48, 0x83, 0xc0, 0x09	[+9 to our jump addr, 9 since prev ins = RIP and target (nop) is +9 ops away]
push rax		//0x50				[Push our modified ret addr to stack]
ret			//0xc3				[Pop return addr into RIP (effectively a jmp))]
.byte 0xe9 		//0xe9				[Trick the disasm again...]
nop			//0x90				[This is our target, can be anything]
```

The disassembly is shown below (objdump)

```bash
0000000000400487 <main>:
  400487:	55                   	push   rbp
  400488:	48 89 e5             	mov    rbp,rsp
  40048b:	e8 01 00 00 00       	call   400491 <L1+0x1>>

0000000000400490 <L1>:
  400490:	e9 58 48 83 c0       	jmp    ffffffffc0c34ced <__TMC_END__+0xffffffffc0633ccd>
  400495:	09 50 c3             	or     DWORD PTR [rax-0x3d],edx
  400498:	e9 90 b8 00 00       	jmp    40bd2d <__FRAME_END__+0xb6f9>
  40049d:	00 00                	add    BYTE PTR [rax],al
  40049f:	5d                   	pop    rbp
  4004a0:	c3                   	ret
  4004a1:	66 2e 0f 1f 84 00 00 	nop    WORD PTR cs:[rax+rax*1+0x0]
  4004a8:	00 00 00
  4004ab:	0f 1f 44 00 00       	nop    DWORD PTR [rax+rax*1+0x0]
```

And in Radare2...

```bash
[0x004003b0]> pdf @ main
            ;-- main:
/ (fcn) main 14
|   main ();
|              ; UNKNOWN XREF from 0x0040048b (main)
|              ; DATA XREF from 0x004003cd (entry0)
|           0x00400487      55             push rbp
|           0x00400488      4889e5         mov rbp, rsp
|           0x0040048b      e801000000     call 0x400491
|           ;-- L1:
\       ,=< 0x00400490      e9584883c0     jmp 0xffffffffc0c34ced
[0x004003b0]> pd 5 @ 0xffffffffc0c34ced
            0xffffffffc0c34ced      ff             invalid
            0xffffffffc0c34cee      ff             invalid
            0xffffffffc0c34cef      ff             invalid
            0xffffffffc0c34cf0      ff             invalid
            0xffffffffc0c34cf1      ff             invalid
[0x004003b0]>
```

As you can see, the disassembly is quite different from the actual assembly above. Both disassemblers have been confused and our code, obfuscated.