# Baserow Formula Language

This directory contains the [ANLTR Grammar](https://www.antlr.org/) for Baserow's custom
formula language.

## Making changes to the language

If you want to make changes to the syntax of the formula language first you must update 
the grammar .g4 files found in this directory. Once done you will then need to be 
re-build the JavaScript and Python3 parsers generated from these grammars and used in 
Baserow's code. To do so run the `./build.sh` which using Docker will generate the 
parsers in the correct locations for you.

