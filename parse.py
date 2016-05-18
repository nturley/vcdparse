from collections import deque


class Command:
    def __init__(self, command_type, command_text):
        self.command_type = command_type
        self.command_text = command_text


class ValueChange:
    def __init__(self, val, sid):
        self.val = val
        self.sid = sid


class SimulationTime:
    def __init__(self, time):
        self.time = time

# 2005 table 18.3
decl_keywords = set('$comment',
                    '$timescale',
                    '$date',
                    '$upscope',
                    '$enddefinitions',
                    '$var',
                    '$scope',
                    '$version')
sim_keywords = set('$dumpall',
                   '$dumpvars',
                   '$dumpon',
                   '$dumpoff')

scalars = ('0', '1', 'x', 'X', 'z', 'Z')
vec_types = ('b', 'B', 'r', 'R')

keywords = decl_keywords + sim_keywords


class StateMachine:

    def __init__(self):
        self.command_type = None
        self.command_text = None
        self.changed_val = None
        self.command_stream = []

    def start_state(self, word, word_stack):
        if word in keywords:
            self.command_type = word
            return self.command_state
        if word.startswith('#'):
            word_stack.appendleft(word[1:])
            return self.time_state
        if word.startswith(scalars):
            self.changed_value = word[0].lower()
            word_stack.appendleft(word[1:])
            return self.vchange_sid_state
        if word.startswith(vec_types):
            self.changed_value = word[0].lower()
            word_stack.appendleft(word[1:])
            return self.vchange_val_state
        assert False

    def command_state(self, word, word_stack):
        if word == '$end':
            command = Command(self.command_type, self.command_text)
            self.command_stream.append(command)
            return self.start_state
        if self.command_text:
            # convert all interior whitespace to a single space
            self.command_text += ' ' + word
        else:
            self.command_text = word
        return self.command_state

    def vchange_sid_state(self, word, word_stack):
        vchange = ValueChange(self.changed_val, word)
        self.command_stream.append(vchange)
        return self.start_state

    def vchange_val_state(self, word, word_stack):
        self.changed_val += word
        return self.vchange_sid_state

    def time_state(self, word, word_stack):
        time = SimulationTime(word)
        self.command_stream.append(time)
        return self.start_state

machine = StateMachine()
next_state = machine.start_state
with open('tests/standard_example.vcd') as f:
    # we parse line by line to avoid holding entire file in memory
    for line in f:
        # we use a deque so we can consume entire words or partial words
        # we push unconsumed characters back into word_stack
        word_stack = deque(line.split())

        # we are mutating word_stack, so we can't iterate
        while len(word_stack) > 0:
            word = word_stack.popleft()
            if len(word) is 0:
                continue
            next_state = next_state(word, word_stack)

print machine.command_stream
