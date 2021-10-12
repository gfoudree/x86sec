---
layout: post
title: "StackSupervisor - a Hypervisor-based Stack Guard"
author: "Grant"
tags: [hypervisor, stack-smashing, buffer overflow, security, kernel, linux]
---

Stack-based buffer overflow attacks have been
around for some time and have been a popular technique for exploiting software. As a result, several mitigation techniques have been proposed and implemented, however none solve the problem completely. This post will demonstrate a new way to detect and protect against kernel-based buffer overflow attacks in guest operating systems using the KVM hypervisor.

# (Some) Existing Stack Smashing Protections:
<hr>
<br>

## DEP or W^X Memory

Data execution protection (DEP) and Write XOR Execute Memory
are the same technique that states that regions of the
executable can be marked as write or executable, but
not both. From a security standpoint, you don’t want
to have regions that can be written to also as marked
as executable. W^X Memory acts as a prevention technique for attackers who inject shellcode
into the stack and attempt to execute it.

The issue with W^X memory is that it does not
prevent return-oriented programming techniques to achieve
arbitrary code execution after a successful stack smashing
attack. Therefore, this technique by itself is not a sufficient
protection.

<!---
#### Return-oriented programming (ROP)
Return-oriented programming, or ROP, is a circumvention technique to the
W^X memory protection. The main concept behind ROP is that instead of loading your shellcode onto the stack and
then returning to it, you reuse code (gadgets) that already
exist inside the binary in a series of return chains. Since
the stack is no longer executable, shellcode you load into it
cannot be returned to and executed, but all the remaining
code inside the compiled binary is fair game since it is
marked as executable. In order to leverage ROP, an attacker
must assemble a series of gadgets from inside the binary.
The criteria for a gadget is that there must be a series of
desirable instructions that end with a RET instruction. By
searching the binary, one can dump various gadgets and
order them in a way to complete the desired operation.
The larger the binary is, the more likely an attacker can
construct a series of gadgets to achieve their goal. Once
they have identified the memory regions of their gadgets,
an attacker overflows the buffer of a vulnerable program,
placing the memory addresses of the gadgets to execute in
reverse order with the first one in the overflowed return
addresses’ spot on the stack. Upon function return, this
chain will be activated and one by one the gadgets will be
executed, each returning to the next in line.

For example, suppose an attacker wanted to invoke
the syscall exit as their exploit to a vulnerable program.
After searching through the program’s binary code, the
following gadgets were extracted:

```bash
0x4004d0: xor %eax, %eax
          ret
0x400100: int $0x80
          ret
0x4FFFFF: inc %eax
          ret
```

In order to call `exit(2)` in 32-bit Linux, the exit code goes
in the EBX register, EAX must be set to 1 for syscall 1
(`exit(2)`), and then interrupt 0x80 fired. Using the above
gadgets, we can achieve this by executing the gadgets in
the following order: `0x4004d0`, `0x4FFFFF`, `0x400100`. To
do this with our stack overflow, we simply need to place
the address of the first gadget (`0x4004d0`) in the original
function’s return address location, followed by `0x4FFFFF`
and `0x400100`.

#### Ret2LibC:
Another technique to circumvent W^X memory is called Ret2LibC and it is similar to ROP
in the sense you are reusing code (libc) to circumvent
the non-executable stack permissions. Like a standard
stack-smashing attack, you need to overflow the buffer and modify the return address. However instead of setting the
return address to your shellcode on the stack, you point it to
an existing function from libc that has been compiled into
the program such as `system(3)`. On 32-bit Linux, parameters
are passed on the stack - which the attacker controls now.
Combining these concepts, an input can be crafted to a
vulnerable program to pass in a command that can be
executed by `system(3)`.
-->

## Stack Canaries

Stack canaries are a popular technique that involves placing a canary value on the stack right before the return
address. The idea is that if a buffer is overrun, given the
order of the stack, a canary placed between the local variables
and the return address will get overwritten before the return
address. If we check if the canary has been modified before
returning from a function, we can infer whether or not a
buffer has been overrun and the return address modified.

<img src="/assets/stack-canary.png" width="50%"/>

Canaries are effective if chosen to be a random value and
the program itself does not have a vulnerability in which
the canary value can be leaked. If this is not the case, an
attacker can simply insert the proper canary (after leaking the
value via a side-channel) in their exploit string in the proper
location as to overflow the buffer, write the exact same canary
value back, followed by the malicious return address. In
addition, stack canaries introduce some additional overhead
in functions due to the checking of the canary value upon
the function returning. For these reasons, stack canaries are good but not entirely perfect.

## ASLR

In order to combat the predictable nature of memory addresses in a program, ASLR was introduced. ASLR stands
for address space layout randomization, and essentially
randomizes the addresses of various regions inside of an
executable. Specifically, ASLR randomizes the address of
the stack and heap when the program is loaded, causing
significant uncertainty when performing a stacking smashing
attack as the return address to which the attacker’s shellcode
exists at changes every execution with high entropy. In
addition to the stack being randomized, other regions such
as the code and dynamic libraries section can be randomized
as well. This makes assembling gadgets for a ROP attack complicated due to the shifting of addresses upon each execution.

ASLR has some weaknesses and, like stack canaries,
if some sort of information leak exists in the program the
addresses of the stack and heap can be leaked and used
by the attacker to discover the proper return address for
their shellcode. Furthermore, some programs that run in a loop without restarting can end up allowing ASLR to be brute-forced
as the randomization occurs when a new process is created.

# Hypervisors
<hr>
<br>

## X86 Privilege Rings

Different regions of memory on an X86 machine execute
with varying levels of privileges. To denote this, the concept
of ”ring versions” is used, with a lower ring indicating a
higher privilege level. For example, an operating system
kernel typically runs at a higher privilege level (ring 0) than
a program running in user-mode inside of that operating
system (ring 3). This concept is important to security as it
prevents user-mode applications from reading and writing to
kernel memory regions and executing privileged instructions.
If this was allowed, user-mode code could escalate privileges
to ring 0 or tamper with privileged memory with disastrous effects.

In order for a hypervisor to isolate and manage guest operating systems, naturally it has to be at a higher privilege level
than the guests it is virtualizing. In the diagram below, you can see that hypervisors run at ring -1. This will be leveraged 
to protect our guest kernel from exploitation as the supervisor code is protected from the OS and has full insight into it. This sort of technique
is also used for [virtual machine introspection](https://en.wikipedia.org/wiki/Virtual_machine_introspection) which is a more expansive way
of monitoring a guest for intrusions and rootkit behavior such as IDT/SSDT hooking.

<br>
<br>
<img src="/assets/cpu-rings.png" width="50%" />

## VT-x/AMD-V

VT-x is Intel’s technology that allows an unmodified guest operating system to run directly on the CPU without emulation, while providing isolation and protection.

When VT-x is being used, there are two modes
the processor can be in, root mode and non-root mode. Root
mode corresponds to the privileged level the virtual machine
monitor (VMM/hypervisor) is running at, and the non-root mode
(non-privileged level) is what the guest operating system is
executing at.

The following steps and figure 4 roughly outline the
life cycle of a hardware virtual machine (HVM) using VT-x:


1. Enable VMX in the CR4 register
2. Initalize VMCS region and run VMXON
3. Write VMCS fields with VMWRITE
4. Start guest with VMLAUNCH
5. Continue guest execution until it exits to VMM
6. Read reason from VMCS via VMREAD
7. Resume execution via VMRESUME or terminate via VMXOFF

In order to maintain the isolation of the guest operating
system, various instructions are not allowed to be executed
by the guest directly. Examples of this are [reading or writing
the paging registers (CR0, CR3), port I/O instructions
(IN/OUT), modifying the IDT and GDT, reading the CPU
timer, external interrupts, reading unauthorized memory
locations, and tamping with the VMX instructions](https://github.com/LordNoteworthy/cpu-internals).
When the guest operating system decides it would like to
perform one of these privileged instructions, it exits into the
hypervisor who emulates the instruction carefully and safely
before returning execution to the guest operating system.

Another concern for guest isolation is direct memory
access (DMA). To combat this, Intel accompanied VT-x
with another technology VT-d, or IOMMU, which is another
technology that prevents memory permissions from being
circumvented via DMA. VT-d can be configured to restrict
which memory regions can be accessed via DMA to prevent malicious behavior.

## Hypercalls

Similar to how userspace programs can execute a
`syscall(2)` to change privilege level and invoke the kernel
by trapping into it, guest operating systems can do the
same to their hypervisor via a hypercall. This mechanism
is used across several hypervisors such as KVM, XEN, and Hyper-V. Each hypervisor has their own
set of hypercalls that they support, making the interfaces
non-portable across different platforms. The corresponding
X86 instruction to invoke a hypercall is `VMCALL` and
can be invoked from the guest operating system kernel or
userspace, trapping into the hypervisor when executed. In
KVM, hypercalls are managed inside the function `int kvm_emulate_hypercall(struct
kvm_vcpu *vcpu)` in the file `arch/x86/kvm/x86.c`. The calling convention involves placing the hypercall number inside of the EAX reg-
ister. Definitions of the hypercall numbers KVM supports are
contained in the header file `include/uapi/linux/kvm_para.h`.
There are alternative methods for the guest to transmit
information to the hypervisor such as memory-mapped IO
(MMIO) and port-mapped IO (PIO), but we'll stick with hypercalls due to the simplicity and ease of use.


## VMENTER/VMEXIT

VMENTER and VMEXIT corresponds to when the CPU
switches from non-root to root mode, or in and out of the
guest operating system. This can occur for many reasons
besides a hypercall. Privileged instructions such as the ones
outlined above in the VT-x section, as well as many other
reasons, can cause a VMEXIT to the hypervisor.
Since it is in the best interest of the VMM to maintain
isolation of the guest, these instructions are trapped and
then emulated by the the VMM. The hypervisor can also
configure some of the instructions that are privileged that it
wants to allow the guest operating system to execute via the
[VMCS fields](https://github.com/LordNoteworthy/cpu-internals/blob/master/VMCS-Layout.pdf). It is also part of the normal execution
process for the VMX preemption timer to expire and fire
a VMEXIT back into the VMM so that virtual machines
can be scheduled. Unfortunately these VMEXIT/VMEMTER
operations are costly and are similar to a context switch by
the kernel when compared to user-mode binaries. When a
VMEXIT occurs, the CPU has to store all of the current
registers into the VMCS, as well as the reason for why the
exit occurred. One [benchmark at AnandTech](https://www.anandtech.com/show/2480/9) shows that
the round-trip time for a VMCALL to VMRESUME can
average about 400ns on a modern processor.

<img src="/assets/vt-x.png" width="60%" />

# Solution
<hr>
<br>

In order to create a robust solution to the stack smashing
problem, we will leverage the higher privilege level
of a hypervisor to monitor the stack frame for overflows
in select functions during kernel execution. Since the
hypervisor has complete control over the guest operating
system, it is able to inspect all of its memory including
the stack. By instructing the protected program to notify
the hypervisor of a function enter/exit, the hypervisor
can inspect/record the stack after entering then validate
the return address before exit. Additionally, this allows
the hypervisor to not only detect that a stack smash has
occurred, but also replace the proper return address on the
stack and heal the program without having it crash.
To do this, we will use a LLVM-pass to insert
the following assembly stub before the RET instruction
and immediately after the stack frame has been setup in
every function.

```bash
mov $0xb, %eax
mov $0x1, %ebx
vmcall ;0x2 for function exit
```

In the above snippet, the first line loads in our custom
hypercall number 0xB into the EAX register. The second
line denotes that we are entering a function (this stub would
go at the beginning of a function) by loading 0x1 into the
EBX register. The value 0x1 would be substituted with
0x2 at the end of a function to signify the end of a call.
Finally, the last line invokes the hypercall and traps into the
hypervisor where we handle the request.

LLVM-passes provide the ability to register callbacks
during program compilation with LLVM which allow the
modification of the generated code. By registering a callback
for each function in the source code, we can traverse the
instructions inside and insert our stub in the proper location.
In order to prevent all functions from being guarded for performance reasons, we can use an attribute that can be set on functions to be protected.

Let's see an example of how this works given the following vulnerable C program:

```c
__attribute__((annotate("StackSupervisor"))) int main() {
char buf[10];
gets(buf);
}
```

Compiled to assembly, we have the following before the
LLVM-pass:

```bash
00000000004004d0 <main>:
    4004d0: push %rbp
    4004d1: mov %rsp,%rbp
    4004d4: sub $0x10,%rsp
    4004d8: lea -0xa(%rbp),%rdi
    4004dc: mov $0x0,%al
    4004de: callq 4003d0 <gets@plt>
    4004e3: xor %ecx,%ecx
    4004e5: mov %eax,-0x10(%rbp)
    4004e8: mov %ecx,%eax
    4004ea: add $0x10,%rsp
    4004ee: pop %rbp
    4004ef: retq
```
After the LLVM-pass with our inserted guard code:

```bash
00000000004004d0 <main>:
    4004d0: push %rbp
    4004d1: mov %rsp,%rbp
    4004d4: sub $0x10,%rsp
    4004d8: mov $0xb,%eax           # Our custom hypercall no. (0xb)
    4004dd: mov $0x1,%ebx           # Hypercall param 0x1 = record
    4004e2: vmcall                  # Invoke hypercall
    4004e5: lea -0xa(%rbp),%rdi
    4004e9: mov $0x0,%al
    4004eb: callq 4003d0 <gets@plt>
    4004f0: mov $0xb,%eax           # Our custom hypercall no. (0xb)
    4004f5: mov $0x2,%ebx           # Hypercall param 0x2 = check
    4004fa: vmcall                  # Invoke hypercall
    4004fd: xor %ecx,%ecx
    4004ff: mov %eax,-0x10(%rbp)
    400502: mov %ecx,%eax
    400504: add $0x10,%rsp
    400508: pop %rbp
    400509: retq
```

We can see that two stubs have been inserted at the
beginning and end of the function. Prior to returning from `main()`, we
have a check to see if the return address on the stack has
been corrupted before jumping to it. At both of the `VMCALL`
instructions, the code traps into our KVM hypercall
interface and we can use various routines inside KVM to
inspect the guest’s state. To read the registers, we can invoke
the KVM function

`long kvm_register_read(struct kvm_vcpu *vcpu, enum kvm_reg reg)`

To read the guest memory (such as the stack), we can call

`int kvm_vcpu_read_guest(struct kvm_vcpu *vcpu, gpa_t gpa, void *data, unsigned long len);`

Armed with the values of the ESP register which points
to the stack and the EBP register which points to the base of
the stack, we can then load this address range into the KVM
function `kvm_vcpu_read_guest()` and read the guest’s stack.
Computing the return address on 32-bit programs is easy
and is at `ebp - 4`. Using this, we can read out the stack as
soon as a function as entered, extract the return address
and keep a copy of it. On the subsequent exit before the `RET`
instruction, we will trap back into our hypercall and do the
same process, comparing the return addresses. If they differ,
we can choose to kill the guest OS, generate some sort of
alert, or attempt to heal the stack by replacing the original
return address onto the stack and resuming execution. In
order to keep track of recursive or nested function calls,
a stack data structure can be used with each function call
resulting in the hypervisor extracting the return address and
storing it on a stack. Subsequent returns would pop off the
appropriate return address for comparison in a LIFO manner.

<!--
## Porting to Userspace Code
<hr>
<br>
As described thus far, StackSupervisor’s protection
applies to a guest operating system running in kernel mode.
With some additional work, however, this technology could
be extended to user-space programs as well if necessary.
The primary issue in doing this is that this would likely
be highly dependent on the guest operating system. Since
the hypervisor does not really have a concept of processes
running inside of the guest, a bridge of some sort would
have to be built between the guest kernel and the hypervisor.
One solution that would work with the Linux operating
system is as follows:

1. Instrument user-mode binary with a similar LLVM-
pass that inserts a syscall() to a custom syscall in the
kernel
2. The custom syscall then records the PID of the process
into a CPU register then invokes a custom hypercall
via vmcall
3. Hypervisor records the stack similar to how it does for
kernel-mode protection, pairing the return address with
the PID communicated from the guest kernel
4. Upon function exit, the same process is followed
syscalling into the kernel, passing the PID into the
hypervisor who then performs the check based on the
PID
5. If the return address differs, the OS can be informed
to kill the process or simply alert on the overflow
-->

# Demo
<hr>
<br>

Let's test StackSupervisor with a simple buffer overflow bug in a very simple 32-bit kernel. We will `memcpy()` a large number of 'a's to overrun a buffer and check that StackSupervisor can detect it.

First let's test a normal function call without an overflow:

```bash
Stackguard Function Enter
RIP=0x100313 RSP=0x104fd0 RBP=0x104fe8
Return address: 0x100389

Stack Dump:
20 00 00 00 00 00 00 00
07 00 00 00 CF 07 00 00
50 00 00 00 19 00 00 00
08 50 10 00 89 03 10 00

Stackguard Function Exit
RIP=0x100343 RSP=0x104fd0 RBP=0x104fe8
Return address: 0x100389
Ret addr OK!

Stack Dump:
FC 03 10 00 15 00 00 00
07 00 00 00 CF 07 00 00
FC 03 10 00 00 00 00 00
08 50 10 00 89 03 10 00
```

As we can see, the return address (0x100389) is not modified. Now let's call our function that overflows our buffer:

```bash
Stackguard Function Enter
RIP=0x1003c0 RSP=0x104fe0 RBP=0x104fe8
Return address: 0x100396

Stack Dump:
3C 19 36 FE 07 00 00 00
08 50 10 00 96 03 10 00
FC 03 10 00 00 00 00 00
00 00 00 00 00 00 00 00

Stackguard Function Exit
RIP=0x1003f4 RSP=0x104fe0 RBP=0x104fe8
Return address: 0xffffffffaaaaaaaa
Return address not equal!!
0x100396 != 0xffffffffaaaaaaaa
 
Stack Dump:
14 00 00 00 07 00 00 AA
AA AA AA AA AA AA AA AA
AA AA AA AA AA AA AA AA
AA AA AA 00 00 00 00 00
```

Looking at dmesg for StackSupervisors output, we observe that a stack corruption has occured.

This is additionally evident by QEMU crashing and we can see that the EIP register has been overwritten with 'aaaaaaaa'.

```bash
KVM internal error. Suberror: 1
emulation failure
EAX=00000000 EBX=00000002 ECX=000b8000
EDX=00000007 ESI=00000000 EDI=0010a000
EBP=aaaaaaaa ESP=00104ff0 EIP=aaaaaaaa
EFL=00010006 [-----P-] CPL=0 II=0 A20=1
SMM=0 HLT=0
```

# Limitations
<hr>
<br>

While StackSupervisor is effective in protecting stack-based attacks, it does not protect from exploits which corrupt
local variables, such as function pointers, to gain arbitrary
code execution. Since an attacker could carefully overflow
a buffer just enough to corrupt a function pointer but not
overwrite the return address. This type of overflow would not
be detected since the return address would not be overrun
which is what StackSupervisor is checking.

# Source Code
<hr>
<br>

Complete Code: [https://github.com/gfoudree/HypervisorStackGuard](https://github.com/gfoudree/HypervisorStackGuard)

KVM Patch: [https://github.com/gfoudree/HypervisorStackGuard/blob/master/kvm.patch](https://github.com/gfoudree/HypervisorStackGuard/blob/master/kvm.patch)