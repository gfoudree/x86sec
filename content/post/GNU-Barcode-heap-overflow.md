---
title: "AFL++: Finding several heap overflows in GNU Barcode 0.99"
date: 2021-09-18T00:00:00-00:00
draft: false
tags: [afl, afl++, fuzzing, gnu barcode, heap overflow, vulnerability, gdb]
categories: []
summary: ""
---
## AFL++


[AFL++](https://github.com/AFLplusplus/AFLplusplus) is an improved version of AFL, a popular and successful fuzzer. In this article we will use it to discover a couple heap-overflow bugs in GNU Barcode 0.99.

## Compiling
It is quite simple to use AFL++, especially if you have access to the source code of the program you are trying to fuzz.

```bash
# Install some deps on Ubuntu
apt install git clang make build-essential gcc-9-plugin-dev

git clone https://github.com/AFLplusplus/AFLplusplus.git
cd AFLplusplus

# Set LLVM_CONFIG to point to your llvm-config binary
LLVM_CONFIG=llvm-config-10 make -j

```

## Building a Target

AFL++ makes it rather easy here - all you have to do is replace `CC`/`CXX` with the `afl-clang-fast`/`afl-clang-fast++` file in your AFL++ build folder and it handles the rest.

For example with GNU Barcode 0.99:

```bash
wget -qO - https://mirrors.sarata.com/gnu/barcode/barcode-0.99.tar.gz | tar vxz
cd barcode-0.99

CC=../AFLplusplus/afl-cc ./configure
make -j

```

## Fuzzing With AFL++

```bash
mkdir /tmp/{in,out}

# Our example input, modify accordingly
# (ex: PNG parser -> copy .png here). Can have multiple files
echo hello > /tmp/in/1

# Run fuzzer
AFLplusplus/afl-fuzz -i /tmp/in/ -o /tmp/out/ -- barcode-0.99/barcode
```
<asciinema-player src="/asciinema_casts/barcode_heapoverflow_afl.cast" cols="110" rows="35"></asciinema-player>

Crash-causing inputs will be found in the `/tmp/out/default/crashes` folder where you can try and reproduce the bug.
<br>
<br>
## Heap Overflows

## Overflow 1


The first overflow I found occured when GNU Barcode tried to parse the following input: 

[`heapoverflow1`](/gnubarcode_heapoverflow1_poc.bin)

```bash
gfoudree@z620 /tmp/poc % xxd < heapoverflow1
00000000: 3109 8000 0a20 3f39 0010 3952 0a47 6847  1.... ?9..9R.GhG
00000010: 6cff 262b 0a                             l.&+.
```

Compiling GNU Barcode with ASAN helps give a hint as to what is going on when the crash occurs.

![heapoverflow1](/gnu_barcode_heapoverflow1_asan.webp "Clang ASAN Output")

Examining this further in GDB, it appears as if the following snippet in `code128.c:443` is responsible for the crash here.

```c

partial = malloc( 6 * len + 4); // 40 bytes allocated

//...

// Far more than 40 bytes are copied into the heap-allocated buffer
for (i=0; i<len; i++) 
	strcat(partial, codeset[codes[i]]);
```

Running the program in GDB while checking the ability to `free()` the buffer `partial` inside of the for loop succeeds several times until it is overflowed and the following output can be seen from PwnDBG:
`
```bash
pwndbg> try_free partial
General checks
Tcache checks
Using tcache_put
Fastbin checks
free(): invalid next size (fast) -> next chunk's size not in [2*size_sz; av->system_mem]
    next chunk's size is 0x3131323234, 2*size_sz is 0x10, system_mem is 0x21000
----------
Free should succeed!
```


The full debugging session demo is shown below.

<asciinema-player src="/asciinema_casts/barcode_heapoverflow_1.cast" cols="120" rows="50"></asciinema-player>
<br>

## Overflow 2

The second one occurs with the following input:

[`heapoverflow2`](/gnubarcode_heapoverflow2_poc.bin)


```bash
gfoudree@z620 /tmp/poc % xxd < heapoverflow2 
00000000: 3109 3100 1000 0039 0010 3944 0a47 6865  1.1....9..9D.Ghe
00000010: 6c80 262b 0a                             l.&+.
```

Here, ASAN gives us an even better hint that a heap overflow is occuring:


![heapoverflow2](/gnu_barcode_heapoverflow2_asan.webp "Clang ASAN Output")


Digging through the source code and running the target in GDB, the source appears to be a different location inside of `code128.c:557`.

```c
// Buffer allocated
textinfo = malloc(12 * (1+strlen(text)/2) + 2);
    
...

textptr = textinfo;

for (i=0, count = 0; i < strlen(text); count++) {
    if (sscanf(text + i, "%u%n", &code, &n) < 1) {
        bc->error = EINVAL; 
            free(partial);
            free(textinfo);
            return -1;
    }
    strcat(partial, codeset[code]);
        
    // ...

    // Overflow occurs here! 
    sprintf(textptr, "%g:9:%c %g:9:%c ", (double)textpos, 
    code >= 100 ? 'A' : code/10 + '0',
    textpos + (double)SYMBOL_WID/2,	code%10 + '0');
    textptr += strlen(textptr);
    textpos += SYMBOL_WID; /* width of each code */
    i += n;
}
```

The loop above continues to copy into the heap-allocated buffer without checking any sort of boundaries, eventually overflowing it.

## Fixes & Conclusion

Over 90 crashing inputs were found after fuzzing GNU Barcode 0.99 for an hour. Of the 2 analyzed above, both are caused by an out-of-bounds write corrupting the heap which causes the subsequent `free()` in the program to operate on a smashed heap causing a crash.

In both instances, a safer function could have been used (`sprintf` -> `snprintf` and `strcpy` -> `strncpy`) which would only copy within the specified bounds and prevented both of these vulnerabilities.