from collections import deque

# simulation or declaration command
class Command:
    def __init__(self, command_type):
        self.comtype = command_type
        self.text = None

    def add_text(self, text):
        if self.text:
            self.text += ' ' + text
        else:
            self.text = text

    def __str__(self):
        if self.text:
            return self.comtype+': '+self.text
        return self.comtype


class ValueChange:
    def __init__(self, val):
        self.val = val
        self.sid = None
    def __str__(self):
        return self.sid+'='+self.val


class SimulationTime:
    def __init__(self, time):
        self.time = time
    def __str__(self):
        return '#' + self.time

# 2005 table 18.3
decl_keywords = set(['$comment',
                    '$timescale',
                    '$date',
                    '$upscope',
                    '$enddefinitions',
                    '$var',
                    '$scope',
                    '$version'])
sim_keywords = set(['$dumpall',
                   '$dumpvars',
                   '$dumpon',
                   '$dumpoff'])

scalars = ('0', '1', 'x', 'X', 'z', 'Z')
vec_types = ('b', 'B', 'r', 'R')

keywords = decl_keywords | sim_keywords


class StateMachine:
    """
    vcd parser state machine
    builds list of commands (Command, ValueChange, or SimulationTime)
    stores completed commands in command_stream
    """

    def __init__(self):
        # partially constructed command
        self.current_command = None
        # list of completed commands
        self.command_stream = []

    def start_state(self, word, word_stack):
        if word in keywords:
            self.current_command = Command(word[1:])
            return self.command_state
        
        # otherwise only consume one character
        # there is no guaranteed whitespace before next token
        word_stack.appendleft(word[1:])
        
        if word.startswith('#'):
            return self.time_state
        
        # otherwise it's one of the value changes
        self.current_command = ValueChange(word[0].lower())

        # scalar values are one character so goto sid
        if word.startswith(scalars):
            return self.vchange_sid_state
        # vector values keep going so goto val before sid
        if word.startswith(vec_types):
            return self.vchange_val_state
        assert False

    def command_state(self, word, word_stack):
        if word == '$end':
            self.command_stream.append(self.current_command)
            return self.start_state
        self.current_command.add_text(word)
        return self.command_state

    def vchange_sid_state(self, word, word_stack):
        self.current_command.sid = word
        self.command_stream.append(self.current_command)
        return self.start_state

    def vchange_val_state(self, word, word_stack):
        self.current_command.val += word
        return self.vchange_sid_state

    def time_state(self, word, word_stack):
        time = SimulationTime(word)
        self.command_stream.append(time)
        return self.start_state

def generate_commands(fname):
    machine = StateMachine()
    next_state = machine.start_state
    with open(fname) as f:
        # only hold one line at a time in memory
        for line in f:
            # we use a deque so we can consume entire words or partial words
            # we pop words and then put unconsumed characters back onto the stack
            word_stack = deque(line.split())

            # we are mutating word_stack, so we can't iterate
            while len(word_stack) > 0:
                word = word_stack.popleft()
                if len(word) is 0:
                    continue

                # execute state, returns next state to execute
                next_state = next_state(word, word_stack)

                # yield any completed commands
                if len(machine.command_stream) > 1:
                    yield machine.command_stream.pop()

if __name__ == '__main__':
    for command in generate_commands('tests/standard_example.vcd'):
        print command