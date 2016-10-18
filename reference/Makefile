TARGETS = gcc_parallel_sort tbb_parallel_sort

.PHONY:
all: $(TARGETS)

.PHONY:
clean:
	rm -f $(wildcard $(TARGETS))

.PHONY:
benchmark: all
	time ./gcc_parallel_sort 2147483647 ../testcase_large/testcase_8G /dev/null
	time ./tbb_parallel_sort 2147483647 ../testcase_large/testcase_8G /dev/null

gcc_parallel_sort: gcc_parallel_sort.cc
	g++ -std=c++11 -fopenmp -O3 $^ -o $@

tbb_parallel_sort: tbb_parallel_sort.cc
	icpc -std=c++11 -ltbb -O3 $^ -o $@
