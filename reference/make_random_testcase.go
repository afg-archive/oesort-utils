package main

import (
	"bufio"
	"fmt"
	"math/rand"
	"os"
)

func check(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, "Error:", err)
		os.Exit(-1)
	}
}

func main() {
	if len(os.Args) != 3 {
		fmt.Fprintf(os.Stderr, "usage: %v filename size\n", os.Args[0])
		os.Exit(-1)
	}
	var size int64
	if _, err := fmt.Sscan(os.Args[2], &size); err != nil || size < 0 {
		fmt.Fprintf(os.Stderr, "%v is not a valid size\n", os.Args[2])
		os.Exit(-1)
	}
	file, err := os.Create(os.Args[1])
	check(err)
	bufwriter := bufio.NewWriter(file)
	_ = bufwriter

	buf := make([]byte, 4)
	for i := int64(0); i < size; i++ {
		rand.Read(buf)
		_, err := bufwriter.Write(buf)
		check(err)
	}

	check(bufwriter.Flush())
	check(file.Close())
}
