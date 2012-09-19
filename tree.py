#!/usr/bin/env python

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

'''
A module for creating tree data structures.

@author: Todd Shore
@version: 2012-01-21
@since: 2012-01-20
@copyright: Copyright 2011--2012 Todd Shore. Licensed for distribution under the Apache License 2.0: See the files "NOTICE" and "LICENSE".
@contact: https://github.com/errantlinguist/PyTree
'''

from copy import deepcopy

def _is_assigned(idx, seq):
    '''
    Checks if a given index has been assigned to an element in a given sequence.
    @param idx: The index to check.
    @param seq: The sequence to check for the index.
    @return: True iff the sequence has the index and the element associated with that index is not None.
    @rtype: bool
    '''
    # If the length of the entry list is equal to or less than the index, it cannot be assigned already
    if len(seq) <= idx:
        return False
    else:
        entry = seq[idx]
        return (entry is not None)
    
def _set_parent(child, parent):
        '''
        Sets the parent of a given child to the given node.
        @param child: The child to set the parent of.
        @param parent: The parent to set.
        '''
        try:
            child.parent = parent
        except AttributeError:
            pass

class Node(object):
    '''
    A node in a tree, with a reference to its parent.
    
    @author: Todd Shore
    @version: 2012-01-21
    @since: 2012-01-20
    '''
    def __init__(self, parent=None):
        '''
        @param parent: The Node parent.
        '''
        # The node parent is the first argument
        self.parent = parent

class NonTerminalNode(Node, list):
    '''
    A non-terminal node in a tree, with references to its children.
    
    @author: Todd Shore
    @version: 2012-01-21
    @since: 2012-01-20
    '''
    def __init__(self, parent=None, *args, **kwargs):
        '''
        @param parent: The Node parent.
        @param args: Any optional positional arguments.
        @param kwargs: Any optional keyword arguments.
        '''
        Node.__init__(self, parent)
        list.__init__(self, *args, **kwargs)
        # Set the child parent
        for child in self:
            _set_parent(child, self)
        
    def __add__(self, iterable):
        error_msg = ("Cannot create a new", self.__class__.__name__, "with the same children as another because the parent reference relationship could not be maintained.")
        raise NotImplementedError(" ".join(error_msg))

    def __iadd__(self, iterable):
        # Make a deep copy of each child to avoid changing the parent of the original child objects
#       iterable = [deepcopy(child) for child in iterable]
        result = super(NonTerminalNode, self).__iadd__(iterable)
        for child in iterable:
            _set_parent(child, self)
            
        return result

    def __deepcopy__(self, memo):
        new_children = [deepcopy(child) for child in self]
        new_node = self.__new__(self.parent, new_children)
        
        return new_node
    
    def __delitem__(self, index):
        deletee = self[index]
        result = super(NonTerminalNode, self).__delitem__(index)
        _set_parent(deletee, None)
        return result
    
    def __delslice__(self, *args, **kwargs):
        deletee_slice = self.__getslice__(*args, **kwargs)
        result = super(NonTerminalNode, self).__delslice__(*args, **kwargs)
        for child in deletee_slice:
            _set_parent(child, None)
        return result

    def __mul__(self, value):
        error_msg = ("Cannot create a new", self.__class__.__name__, "with the same children as another because the parent reference relationship could not be maintained.")
        raise NotImplementedError(" ".join(error_msg))

    def __setitem__(self, index, child):
        result = super(NonTerminalNode, self).__setitem__(index, child)

        _set_parent(child, self)
        return result
    
    def __setslice__(self, start, stop, seq):
        result = super(NonTerminalNode, self).__setslice__(start, stop, seq)        
        # Calcuate the number of new children added, even if the total child count is lower after setting the slice
        new_child_count = min(stop - start -1, len(seq))
        # Get the newly-added children
        new_children = self[start : start + new_child_count]
        # Update the parent reference for all newly-added children
        for child in new_children:
            _set_parent(child, self)
            
        return result
        
    def __repr__(self):
        # super() not used here to specifically pick the list.__repr__ over any other superclasses this class inherits from in multiple inheritance
        repr_tuple = (self.__class__.__name__, "(", list.__repr__(self), ")")
        return ''.join(repr_tuple)  
    
    def __str__(self):
        # super() not used here to specifically pick the list.__repr__ over any other superclasses this class inherits from in multiple inheritance
        str_tuple = (self.__class__.__name__, "(children=", list.__repr__(self), ")")
        return ''.join(str_tuple)  

    def append(self, child):
        result = super(NonTerminalNode, self).append(child)
        _set_parent(child, self)
        return result
    
    def extend(self, iterable):
        result = super(NonTerminalNode, self).extend(iterable)
        for child in iterable:
            _set_parent(child, self)
        return result
    
    def pop(self, *args, **kwargs):
        child = super(NonTerminalNode, self).pop(*args, **kwargs)
        _set_parent(child, None)
        return child

class BiDirectionalLookupNonTerminalNode(NonTerminalNode):
    '''
    A node in a tree data structure which allows both the looking up of a child by its index as well as looking up the index of a child by a reference to the child itself.
    NOTE: The child childects cannot be of type ``int``, because integers are always considered to be __indices. Similarly, all list items must be unique because each item is a key in the reverse-lookup dictionary.
    
    @author: Todd Shore
    @version: 2012-01-21
    @since: 2012-01-20
    '''
    
    def __init__(self, parent=None, *args, **kwargs):
        '''
        @param parent: The Node parent.
        @param args: Any additional arguments, the first thereof (args[0]) being used to initialise the Node with items therefrom.
        @param kwargs: Any named arguments.
        '''
        # super() not used here to avoid problems with subclasses
        NonTerminalNode.__init__(self, parent, *args, **kwargs)

        self.__indices = {}

        # Build index map
        for index, child in enumerate(self):
            self.__indices[child] = index
                
        self.__last_automatically_added_index = -1
            
    def __delitem__(self, index):
        deletee = super(BiDirectionalLookupNonTerminalNode, self).__getitem__(index)
        
        result = super(BiDirectionalLookupNonTerminalNode, self).__delitem__(index)
        
        self.__delete_from_indices(deletee)
        self.__update_dict_indices(index+1, len(self), -1)
        
        return result
        
    def __delslice__(self, start, stop):
        
        deletee_slice = self[start:stop]
        
        result = super(BiDirectionalLookupNonTerminalNode, self).__delslice__(start, stop)
        
        # Clear the index dictionary of the deleted children
        for deletee in deletee_slice:
            self.__delete_from_indices(deletee)
        
        # Update the entries in the index dictionary
        shift_value = len(deletee_slice) * -1
        self.__update_dict_indices(start, stop, shift_value)
        
        return result
    
#    def __getitem__(self, value):
#        if isinstance(value, int):
#            item = super(BiDirectionalLookupNonTerminalNode, self).__getitem__(value)
#        elif isinstance(value, Node):
#            # If the value given is actually a Node, return is index. This is done to mimic true dictionary syntax.
#            item = self.index(value)
#        else:
#            raise TypeError("Given index must be an instance of either int or Node; Type: " + str(type(value)))
#        
#        return item
    
    def __iadd__(self, iterable):
        original_len = len(self)
        
        result = super(BiDirectionalLookupNonTerminalNode, self).__iadd__(iterable)
        
        for index, child in enumerate(iterable):
            # Get the index of the newly-added child in the node
            index = index + original_len
            self.__indices[child] = index
    
        return result

    def __imul__(self, *args, **kwargs):
        raise NotImplementedError("Cannot multiply items because each child must be unique (i.e. not a duplicate of another).")
    
    def __mul__(self, *args, **kwargs):
        raise NotImplementedError("Cannot multiply items because each child must be unique (i.e. not a duplicate of another).")

    def __rmul__(self, *args, **kwargs):
        raise NotImplementedError("Cannot multiply items because each child must be unique (i.e. not a duplicate of another).")
        
    def __setitem__(self, index, child):
        if len(self) > index:
            replacee = super(BiDirectionalLookupNonTerminalNode, self).__getitem__(index)
            
            result = super(BiDirectionalLookupNonTerminalNode, self).__setitem__(index, child)
            # Remove the replaced child from the reverse-lookup map
            self.__delete_from_indices(replacee)
        
            self.__indices[child] = index
            
        else:
            self.__ensure_valid_index(index)
            result = super(BiDirectionalLookupNonTerminalNode, self).__setitem__(index, child)
            
        return result
            
        
    def __setslice__(self, start, stop, seq):
        replacee_slice = self[start:stop]
        
        result = super(BiDirectionalLookupNonTerminalNode, self).__setslice__(start, stop, seq)
        
        # Clear the index dictionary of the items to replace
        for replacee in replacee_slice:
            self.__delete_from_indices(replacee) 
        
        # Add the new items to the index dictionary
        replaced_item_index = start
        seq_item_index = 0
        while replaced_item_index < stop:
            item = seq[seq_item_index]
            self.__indices[item] = replaced_item_index
        
            replaced_item_index += 1
            seq_item_index += 1
            
        return result
    
    def __delete_from_indices(self, child):
        '''
        Deletes a child and its index from the index dictionary, while avoiding any KeyErrors from trying to delete ``None`` when deleting empty list elements.
        @param child: The child to delete from the index dictionary.
        '''
        try:
            del self.__indices[child]
        except KeyError:
            # Catch key errors from deleting ``None`` items
            pass
        
    def __ensure_valid_index(self, index):
        '''
        Ensures that an index can be retrieved by appending ``None`` items if the length is not long enough.
        @param index: The index of which to ensure the existence.
        '''
        while len(self) <= index:
            # super() not used here to avoid problems from multiple inheritance
            super(BiDirectionalLookupNonTerminalNode, self).append(None)
            
    def __get_next_free_index(self):
        '''
        Gets the next free index, i.e. the index of the first ``None`` childect or the end of the children list (len(self)).
        @return: The next free index.
        @rtype: int
        '''
        next_free_index = self.__last_automatically_added_index + 1
        while _is_assigned(next_free_index, self):
            print next_free_index
            next_free_index += 1
            
        return next_free_index

    def __update_dict_indices(self, start, stop, shift_value):
        '''
        Updates the index in the index dictionary of a slice of children which had been previously moved.
        @param start: The slice start index.
        @param stop: The slice stop index.
        @param shift_value: The value to shift the respective index in the index dictionary for each child by.
        '''
        items_to_update = super(BiDirectionalLookupNonTerminalNode, self).__getslice__(start, stop) 
        for item in items_to_update:
            self.__indices[item] += shift_value

    def append(self, child):
        index = self.__get_next_free_index()
        self[index] = child
        self.__last_automatically_added_index = index

    def count(self, value):
        if value in self.__indices:
            return 1
        elif value is None:
            return super(BiDirectionalLookupNonTerminalNode, self).count(value)
        else:
            return 0
        
    def extend(self, iterable):
        for child in iterable:
            self.append(child)

    def index(self, child):
        return self.__indices[child]
    
    @property
    def indices(self):
        return self.__indices
    
    def insert(self, index, child):
        self.__update_dict_indices(index, len(self), 1)
        
        super(BiDirectionalLookupNonTerminalNode, self).insert(index, child)
        
        if child is not None:
            self.__indices[child] = index
        
    def pop(self, *args, **kwargs):
        item = super(BiDirectionalLookupNonTerminalNode, self).pop(*args, **kwargs)
        del self.__indices[item]
        return item
    
    def remove(self, item):
        index = self.__indices[item]
        del self[index]
    
    def reverse(self, *args, **kwargs):
        super(BiDirectionalLookupNonTerminalNode, self).reverse(*args, **kwargs)
        for index, item in enumerate(self):
            self.__indices[item] = index
            
    def sort(self, cmp=None, key=None, reverse=False):
        super(BiDirectionalLookupNonTerminalNode, self).sort(cmp=None, key=None, reverse=False)
        for index, item in enumerate(self):
            self.__indices[item] = index
            
