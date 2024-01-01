"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import JackTokenizer
import SymbolTable
import VMWriter

STATEMENTS = {"let", "while", "if", "do", "return"}
OPS = {'+', '-', '*', '/', '&', '|', '<', '>', '=', "&lt;", "&gt;", "&amp;"}
BIN_OPS_DICT = {
    '+': 'ADD',
    '-': 'SUB',
    '=': 'EQ',
    '&gt;': 'GT',
    '&lt;': 'LT',
    '&amp;': 'AND',
    '|': 'OR',
}
UNARY = {'#', '^', '~', '-'}
UNARY_OPS_DICT = {
    '-': 'NEG',
    '~': 'NOT',
    '^': 'SHIFTLEFT',
    '#': 'SHIFTRIGHT'
}
label_names = {
    "SYMBOL": "symbol",
    "STRING_CONST": "stringConstant",
    "INT_CONST": "integerConstant",
    "KEYWORD": "keyword",
    "IDENTIFIER": "identifier"
}


class CompilationEngine:
    """Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """

    def __init__(self, input_stream: "JackTokenizer",
                 table: "SymbolTable", writer: "VMWriter") -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        """
        # Your code goes here!
        # Note that you can write to output_stream like so:
        # output_stream.write("Hello world! \n")
        self.tkn = input_stream
        self.table = table
        self.writer = writer
        self.out = writer.out
        self.outerFuncName = ""

        self.get_name = {
            "IDENTIFIER": self.tkn.identifier,
            "KEYWORD": self.tkn.keyword,
            "SYMBOL": self.tkn.symbol,
            "STRING_CONST": self.tkn.string_val,
            "INT_CONST": self.tkn.int_val
        }
        self.statement_dict = {
            "let": self.compile_let,
            "if": self.compile_if,
            "do": self.compile_do,
            "while": self.compile_while,
            "return": self.compile_return
        }

        self.class_name = None
        self.whiles = -1
        self.ifs = -1

    def my_advance(self):
        if self.tkn.has_more_tokens():
            self.tkn.advance()

    def write_binary_op(self, binary_op):
        if binary_op == "*":
            self.writer.write_call("Math.multiply", 2)
        elif binary_op == "/":
            self.writer.write_call("Math.divide", 2)
        elif binary_op:
            self.writer.write_arithmetic(BIN_OPS_DICT[binary_op])

    def compile_class(self) -> None:
        """Compiles a complete class."""
        # Your code goes here!

        self.my_advance()
        self.class_name = self.get_name[self.tkn.token_type()]()
        self.my_advance()
        self.my_advance()
        if self.tkn.keyword() in {"field", "static"}:
            self.compile_class_var_dec()

        if self.tkn.keyword() in {"constructor", "function", "method"}:
            self.compile_subroutine()

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""
        # Your code goes here!
        class_var = True
        while class_var:
            # static / field:
            curr_kind = self.get_name[
                self.tkn.token_type()]().upper()  # STATIC or FIELD
            self.my_advance()
            # int, char, boolean, className

            curr_type = self.get_name[self.tkn.token_type()]()
            self.my_advance()
            while self.tkn.token_type() != "KEYWORD":  # in case of x, y, z ...
                curr_name = self.get_name[self.tkn.token_type()]()
                if curr_name not in {",", ";"}:
                    self.table.define(curr_name, curr_type, curr_kind)
                self.my_advance()
            # now we can assume token type is keyword
            if self.tkn.keyword() not in {"field", "static"}:
                class_var = False

    def compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        subroutine = True
        while subroutine:
            function_type = self.tkn.keyword()
            if function_type == "method":
                self.table.define("this", self.class_name, "ARG")
            self.my_advance()
            self.my_advance()
            self.outerFuncName = self.class_name + "."
            self.outerFuncName += self.tkn.identifier()
            self.my_advance()
            self.my_advance()
            self.compile_parameter_list()
            self.my_advance()
            self.compile_subroutine_body(function_type)
            self.table.start_subroutine()
            if self.get_name[self.tkn.token_type()]() not in {"constructor",
                                                              "function",
                                                              "method"}:
                subroutine = False
            self.ifs = -1
            self.whiles = -1

    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        # Your code goes here!
        curr_type = None
        while self.get_name[self.tkn.token_type()]() != ")":
            if self.get_name[self.tkn.token_type()]() != ",":
                if not curr_type:
                    curr_type = self.get_name[self.tkn.token_type()]()
                else:
                    self.table.define(self.get_name[self.tkn.token_type()](),
                                      curr_type, "ARG")
                    curr_type = None
            self.my_advance()

    def write_beginning(self, function_type) ->None:
        if function_type == "constructor":
            self.writer.write_push("CONST", self.table.var_count("FIELD"))
            self.writer.write_call("Memory.alloc", 1)
            self.writer.write_pop("POINTER", 0)
        if function_type == "method":
            self.writer.write_push("ARG", 0)
            self.writer.write_pop("POINTER", 0)

    def compile_subroutine_body(self, function_type) -> None:

        self.my_advance()
        self.compile_var_dec()
        self.write_beginning(function_type)
        self.compile_statements()
        self.my_advance()

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        # Your code goes here!
        curr_type = None
        count = 0
        while self.tkn.token_type() == "KEYWORD" and \
                self.get_name[self.tkn.token_type()]() == "var":
            self.my_advance()
            semicolon = False
            first = True
            while not semicolon:
                if first:
                    curr_type = self.get_name[self.tkn.token_type()]()
                    first = False
                else:
                    if self.tkn.token_type() != "SYMBOL":
                        self.table.define(
                            self.get_name[self.tkn.token_type()](), curr_type,
                            "VAR")
                        count += 1
                if self.get_name[self.tkn.token_type()]() == ";":
                    semicolon = True
                self.my_advance()
        self.writer.write_function(self.outerFuncName, count)
        self.outerFuncName = ""

    def compile_statements(self) -> None:
        """Compiles a sequence of statements, not including the enclosing 
        "{}".
        """
        # Your code goes here!
        while self.tkn.token_type() == "KEYWORD" and \
                self.get_name[self.tkn.token_type()]() in STATEMENTS:
            self.statement_dict[self.tkn.keyword()]()

    def compile_do(self) -> None:
        """Compiles a do statement."""
        # Your code goes here!
        n_args = 0
        self.my_advance()
        lookahead = [self.tkn.token_type(),
                     self.get_name[self.tkn.token_type()]()]
        self.my_advance()
        if self.tkn.symbol() == ".":  # we know it is a symbol
            if self.table.type_of(lookahead[1]):
                self.outerFuncName+=self.table.type_of(lookahead[1])
                self.writer.write_push(self.table.kind_of(lookahead[1]),
                                       self.table.index_of(lookahead[1]))
                n_args+=1
            else:
                self.outerFuncName += lookahead[1]
            self.my_advance()
            lookahead = [self.tkn.token_type(),
                         self.get_name[self.tkn.token_type()]()]
            self.my_advance()
        else:
            self.outerFuncName +=self.class_name
            self.writer.write_push("POINTER", 0)
            n_args += 1
        self.outerFuncName += "."
        self.outerFuncName += lookahead[1]
        self.my_advance()
        n_args += self.compile_expression_list()
        self.writer.write_call(self.outerFuncName, n_args)
        self.outerFuncName= ""
        self.my_advance()
        self.writer.write_pop("TEMP", 0)
        self.my_advance()

    def compile_let(self) -> None:
        """Compiles a let statement."""

        self.my_advance()
        lhs = self.get_name[self.tkn.token_type()]()
        self.my_advance()
        if self.tkn.symbol() == "[":  # todo: arrays
            self.my_advance()
            self.compile_expression()
            self.writer.write_push(self.table.kind_of(lhs), self.table.index_of(lhs))
            self.writer.write_arithmetic("ADD")
            self.my_advance()
            self.my_advance()
            self.compile_expression()
            self.writer.write_pop("TEMP", 0)
            self.writer.write_pop("POINTER", 1)
            self.writer.write_push("TEMP", 0)
            self.writer.write_pop("THAT", 0)
            self.my_advance()

        else:
            self.my_advance()
            self.compile_expression()
            self.writer.write_pop(self.table.kind_of(lhs),
                                  self.table.index_of(lhs))
            self.my_advance()

    def compile_while(self) -> None:
        """Compiles a while statement."""
        # Your code goes here!
        self.whiles += 1
        index = str(self.whiles)
        self.writer.write_label("WHILE_EXP" + index)
        self.my_advance()
        self.my_advance()
        self.compile_expression()
        self.writer.write_arithmetic("NOT")
        self.writer.write_if("WHILE_END" +index)
        self.my_advance()
        self.my_advance()
        self.compile_statements()
        self.my_advance()
        self.writer.write_goto("WHILE_EXP" + index)
        self.writer.write_label("WHILE_END" + index)

    def compile_return(self) -> None:
        """Compiles a return statement."""
        # Your code goes here!
        self.my_advance()
        if self.tkn.token_type() != "SYMBOL" or \
                (self.tkn.token_type() == "SYMBOL" and self.get_name[
                    self.tkn.token_type()]() != ";"):
            self.compile_expression()
        else:
            self.writer.write_push("CONST", 0)
        self.writer.write_return()
        self.my_advance()

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        # Your code goes here!
        self.ifs+=1
        index = str(self.ifs)
        self.my_advance()
        self.my_advance()
        self.compile_expression()
        self.writer.write_if("IF_TRUE"+index)
        self.writer.write_goto("IF_FALSE"+index)
        self.writer.write_label("IF_TRUE"+index)
        self.my_advance()
        self.my_advance()
        self.compile_statements()
        self.my_advance()
        if self.tkn.token_type() == "KEYWORD":
            if self.tkn.keyword() == "else":
                self.writer.write_goto("IF_END" + index)
                self.writer.write_label("IF_FALSE"+index)
                self.my_advance()
                self.my_advance()
                self.compile_statements()
                self.my_advance()
                self.writer.write_label("IF_END" + index)
            else:
                self.writer.write_label("IF_FALSE"+index)
        else:
            self.writer.write_label("IF_FALSE" + index)
        # self.out.write("</ifStatement>\n")

    def compile_expression(self) -> None:
        """Compiles an expression."""
        # Your code goes here!
        unary_op = None
        if self.get_name[self.tkn.token_type()]() in UNARY:
            unary_op = self.get_name[self.tkn.token_type()]()
            self.my_advance()
        self.compile_term()
        if unary_op:
            self.writer.write_arithmetic(UNARY_OPS_DICT[unary_op])
        unary_op = None
        binary_op = None
        while self.get_name[self.tkn.token_type()]() in OPS:
            binary_op = self.get_name[self.tkn.token_type()]()
            self.my_advance()
            if self.get_name[self.tkn.token_type()]() in UNARY:
                unary_op = self.get_name[self.tkn.token_type()]()
                self.my_advance()
            self.compile_term()
            if unary_op:
                self.writer.write_arithmetic(UNARY_OPS_DICT[unary_op])
                unary_op = None
            self.write_binary_op(binary_op)

    def compile_term(self) -> None:
        """Compiles a term. 
        This routine is faced with a slight difficulty when
        trying to decide between some of the alternative parsing rules.
        Specifically, if the current token is an identifier, the routing must
        distinguish between a variable, an array entry, and a subroutine call.
        A single look-ahead token, which may be one of "[", "(", or "." suffices
        to distinguish between the three possibilities. Any other token is not
        part of this term and should not be advanced over.
        """
        # Your code goes here!
        cur_func_name =""
        lookahead = [self.tkn.token_type(),
                     self.get_name[self.tkn.token_type()]()]
        self.my_advance()
        if self.get_name[self.tkn.token_type()]() == "(" \
                and lookahead[1] != "(":

            # lookahead[1] is the name of a function

            self.my_advance()
            n_args = self.compile_expression_list()
            self.writer.write_call(lookahead[1], n_args)
            self.my_advance()

        elif self.get_name[self.tkn.token_type()]() == ".":
            n_args =0
            if self.table.type_of(lookahead[1]):
                cur_func_name +=self.table.type_of(lookahead[1])
                cur_func_name +='.'
                self.writer.write_push(self.table.kind_of(lookahead[1]),
                                       self.table.index_of(lookahead[1]))
                n_args+=1
                self.my_advance()
            else:
                cur_func_name +=lookahead[1]
                cur_func_name +='.'
                self.my_advance()
            cur_func_name += self.get_name[self.tkn.token_type()]()
            self.my_advance()
            self.my_advance()
            n_args += self.compile_expression_list()
            self.my_advance()
            self.writer.write_call(cur_func_name, n_args)
            # self.outerFuncName=""
            # self.my_advance()

        elif lookahead[1] == "(":  # for expression in parentheses
            # self.out.write("<symbol> ( </symbol>\n")
            self.compile_expression()
            # self.out.write("<symbol> ) </symbol>\n")
            self.my_advance()
        else:
            # self.out.write(  # writing the varName / className
            #     "<{}> {} </{}>\n".format(
            #         label_names[lookahead[0]],
            #         lookahead[1],
            #         label_names[lookahead[0]]))
            if lookahead[0] == "INT_CONST":
                self.writer.write_push("CONST", int(lookahead[1]))
            elif lookahead[0] == "KEYWORD":
                if lookahead[1] == "null" or lookahead[1] == "false":
                    self.writer.write_push("CONST", 0)
                if lookahead[1] == "true":
                    self.writer.write_push("CONST", 0)
                    self.writer.write_arithmetic("NOT")
                if lookahead[1] == "this":
                    self.writer.write_push("POINTER", 0)

            elif lookahead[0] == "STRING_CONST":
                self.writer.write_push("CONST", len(lookahead[1]))
                self.writer.write_call("String.new", 1)
                for char in lookahead[1]:
                    self.writer.write_push("CONST", ord(char))
                    self.writer.write_call("String.appendChar", 2)
            elif self.get_name[self.tkn.token_type()]() == "[":  # todo: arrays
                self.my_advance()
                self.compile_expression()
                self.writer.write_push(self.table.kind_of(lookahead[1]),
                                       self.table.index_of(lookahead[1]))
                self.writer.write_arithmetic("ADD")
                # self.writer.write_pop("TEMP", 0)
                self.writer.write_pop("POINTER",1)
                # self.writer.write_push("TEMP", 0)
                self.writer.write_push("THAT", 0)

                self.my_advance()

            else:  # it is an identifier
                self.writer.write_push(self.table.kind_of(lookahead[1]),
                                       self.table.index_of(lookahead[1]))



    def compile_expression_list(self) -> int:
        """Compiles a (possibly empty) comma-separated list of expressions."""
        # Your code goes here!
        count = 0
        while self.tkn.token_type() != 'SYMBOL' or \
                (self.tkn.token_type() == 'SYMBOL' and self.get_name[
                    self.tkn.token_type()]() != ")"):
            if self.tkn.token_type() == 'SYMBOL' and \
                    self.get_name[self.tkn.token_type()]() == ",":
                self.my_advance()
            else:
                self.compile_expression()
                count += 1

        # self.out.write("</expressionList>\n")
        return count
