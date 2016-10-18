// compile this with -ltbb

#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

#include <parallel/algorithm>

int main(int argc, char** argv) {
    std::ios_base::sync_with_stdio(false);
    if (argc != 4) {
        std::cerr << "usage: " << argv[0] << " size input output\n";
        return -1;
    }
    std::istringstream iss(argv[1]);
    size_t size;
    if (not (iss >> size)) {
        std::cerr << "argument 1 " << argv[1] << " is not a valid size\n";
        return -1;
    }
    std::ifstream inputfile(argv[2]);
    if (not inputfile) {
        std::cerr << "bad input file: " << argv[2] << "\n";
        return -1;
    }
    std::ofstream outputfile(argv[3]);
    if (not outputfile) {
        std::cerr << "bad output file: " << argv[3] << "\n";
        return -1;
    }
    auto buffer = new int[size];
    inputfile.read((char*)buffer, size * sizeof(int));
    __gnu_parallel::sort(buffer, buffer + size);
    outputfile.write((char*)buffer, size * sizeof(int));
}
