"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class SymbolTable:
    """A symbol table that associates names with information needed for Jack
    compilation: type, kind and running index. The symbol table has two nested
    scopes (class/subroutine).
    """

    def __init__(self) -> None:
        """Creates a new empty symbol table."""
        # Your code goes here!

        self.static_dict = {}
        self.arg_dict = {}
        self.field_dict = {}
        self.var_dict = {}
        # self.dict_of_dicts = {
        #     "STATIC": self.static_dict,
        #     "FIELD": self.field_dict,
        #     "ARG": self.arg_dict,
        #     "VAR": self.var_dict
        # }

    def start_subroutine(self) -> None:
        """Starts a new subroutine scope (i.e., resets the subroutine's 
        symbol table).
        """
        # Your code goes here!

        self.arg_dict = {}
        self.var_dict = {}

    def define(self, name: str, type: str, kind: str) -> None:
        """Defines a new identifier of a given name, type and kind and assigns 
        it a running index. "STATIC" and "FIELD" identifiers have a class scope, 
        while "ARG" and "VAR" identifiers have a subroutine scope.

        Args:
            name (str): the name of the new identifier.
            type (str): the type of the new identifier.
            kind (str): the kind of the new identifier, can be:
            "STATIC", "FIELD", "ARG", "VAR".
        """
        # Your code goes here!
        # curr_dict = self.dict_of_dicts[kind]
        if kind == "VAR":
            self.var_dict[name] = (type, len(self.var_dict))
        if kind == "ARG":
            self.arg_dict[name] = (type, len(self.arg_dict))
        if kind == "STATIC":
            self.static_dict[name] = (type, len(self.static_dict))
        if kind == "FIELD":
            self.field_dict[name] = (type, len(self.field_dict))



    def var_count(self, kind: str) -> int:
        """
        Args:
            kind (str): can be "STATIC", "FIELD", "ARG", "VAR".

        Returns:
            int: the number of variables of the given kind already defined in 
            the current scope.
        """
        # Your code goes here!
        if kind == "ARG":
            return len(self.arg_dict)
        if kind == "STATIC":
            return len(self.static_dict)
        if kind == "VAR":
            return len(self.var_dict)
        if kind == "FIELD":
            return len(self.field_dict)


    def kind_of(self, name: str) -> str:
        """
        Args:
            name (str): name of an identifier.

        Returns:
            str: the kind of the named identifier in the current scope, or None
            if the identifier is unknown in the current scope.
        """
        # Your code goes here!
        if name in self.var_dict.keys():
            return "LOCAL"
        if name in self.arg_dict.keys():
            return "ARG"
        if name in self.static_dict.keys():
            return "STATIC"
        if name in self.field_dict.keys():
            return "THIS"
        return "NONE"

    def type_of(self, name: str) -> str:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            str: the type of the named identifier in the current scope.
        """
        # Your code goes here!
        if name in self.var_dict.keys():
            return self.var_dict[name][0]
        if name in self.arg_dict.keys():
            return self.arg_dict[name][0]
        if name in self.static_dict.keys():
            return self.static_dict[name][0]
        if name in self.field_dict.keys():
            return self.field_dict[name][0]

    def index_of(self, name: str) -> int:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            int: the index assigned to the named identifier.
        """
        # Your code goes here!
        if name in self.var_dict.keys():
            return self.var_dict[name][1]
        if name in self.arg_dict.keys():
            return self.arg_dict[name][1]
        if name in self.static_dict.keys():
            return self.static_dict[name][1]
        if name in self.field_dict.keys():
            return self.field_dict[name][1]