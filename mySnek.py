import socket
import random
import time

TCP_IP = '51.12.57.196'
TCP_PORT = 4000
BUFFER_SIZE = 1024

class Limit:
    def __init__(self, lowerPos, upperPos):
        self.lowerPos = lowerPos
        self.upperPos = upperPos

    def __lt__(self, other):
        return self.lowerPos < other.lowerPos
    
    def __str__(self):
        return str(self.lowerPos) + ' - ' + str(self.upperPos)
    
    def isInside(self, pos):
        return pos >= self.lowerPos and pos <= self.upperPos    
    
    def isAtLeftSide(self, pos):
        return pos.x == self.lowerPos.x
    
    def isAtRightSide(self, pos):
        return pos.x == self.upperPos.x
    
    def isAtTopSide(self, pos):
        return pos.y == self.upperPos.y
    
    def isAtBottomSide(self, pos):
        return pos.y == self.lowerPos.y

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def left(self, limit):
        if limit.isAtLeftSide(self):
            return Position(limit.upperPos.x,self.y)
        else:
            return Position(self.x-1,self.y) 
        
    def up(self, limit):
        if limit.isAtTopSide(self):
            return Position(self.x, limit.lowerPos.y)
        else:
            return Position(self.x,self.y-1) 
        
    def right(self, limit):
        if limit.isAtRightSide(self):
            return Position(limit.lowerPos.x,self.y)
        else:
            return Position(self.x+1,self.y) 
        
    def down(self, limit):
        if limit.isAtBottomSide(self):
            return Position(self.x, limit.lowerPos.y)
        else:
            return Position(self.x,self.y+1) 
        
    def __lt__(self, other):
        if self.y < other.y:
            return True
        elif self.y == other.y:
            return self.x < other.x
        else:
            return False
        
    def __str__(self):
        return '(' + str(self.x) + ', ' + str(self.y) + ')'

    def getNextToPositions(self, limit):
        return [self.left(limit), self.up(limit), self.right(limit), self.down(limit)]
        
class Snek:
    def __init__(self):
        self.play()

    def startGame(self, width, height, player_id):
        self.width = width
        self.height = height
        self.player_id = player_id
        self.covered_spaces = []
        self.numberOfPlayers = 0
        self.alive = True
        self.covered_spaces_by = []
        self.others_possible_next_move = []

        
    def checkDirections(self, covered):
        # print('covered: ' + str(covered))
        possible_directions = [b'left', b'up', b'right', b'down']
        if self.mypos.left(self.limit) in covered:
            possible_directions.remove(b'left')
        if self.mypos.up(self.limit) in covered:
            possible_directions.remove(b'up')
        if self.mypos.right(self.limit) in covered:
            possible_directions.remove(b'right')
        if self.mypos.down(self.limit) in covered:
            possible_directions.remove(b'down')
        
        return possible_directions

    def remove(self, index):
        y = self.covered_spaces_by[int(index)]
        # print("Want to remove: " + str(index) + ' with ' + str(y))
        # print("before: " + str(self.covered_spaces))
        self.covered_spaces = [i for i in self.covered_spaces if i not in y]
        # print("after: " + str(self.covered_spaces))


    def connect(self, BUFFER_SIZE=1024):
        try:
            # Create a socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f"Socket created: {self.socket}")

            # Connect to the server
            self.socket.connect((TCP_IP, TCP_PORT))

            # Receive data
            reply = self.socket.recv(BUFFER_SIZE).decode('utf-8')
            print(f"Received reply: {reply}")

            return reply
        except socket.gaierror as e:
            print(f"Address-related error: {e}")
        except socket.error as e:
            print(f"Socket error: {e}")
        finally:
            # Always close the socket
            if 'sock' in locals():
                self.socket.close()
                print("Socket closed")


    def play(self):
        counter = 0
        answer = ''
        while counter > 10000 or not "documentation" in answer:
            time.sleep(1)
            answer = self.connect()
            print(answer)

        if "documentation" in answer:
            self.socket.send(b'join|kurisu|' + str.encode('NewPass23') + b'\n')
            print('joined')
            while True:
                possible_directions = []
                msg = self.socket.recv(BUFFER_SIZE)
                msgs = msg.split(b'\n')
                msgs = [m for m in msgs if m != b'']
                for m in msgs:
                    # print(m)
                    if m.startswith(b'game'):
                        game = m.split(b'|')
                        self.startGame(int(game[1]), int(game[2]), int(game[3]))
                    elif m.startswith(b'pos'):
                        pos = m.split(b'|')
                        if len(pos) >= 4 and '' not in pos:
                            player_id = int(pos[1])
                            p = Position(int(pos[2]), int(pos[3]))
                            self.covered_spaces.append(p)
                            self.covered_spaces_by[player_id].append(p)
                            if player_id == self.player_id:
                                self.mypos = p
                            else:
                                self.others_possible_next_move += p.getNextToPositions(self.limit)
                        else:
                            print('received invalid pos')
                    elif m.startswith(b'tick'):
                        self.covered_spaces.sort()
                        self.others_possible_next_move.sort()
                        better_directions = self.checkDirections(self.covered_spaces + self.others_possible_next_move)
                        print('Better Directions: ' + str(better_directions))
                        if better_directions != []:
                            move = random.choice(better_directions)
                            print('Better MOVE SENDED: ' + str(move))                            
                        else:
                            possible_directions = self.checkDirections(self.covered_spaces)
                            if possible_directions != []:
                                move = random.choice(possible_directions)
                                print('Possible Directions: ' + str(possible_directions))
                                print('Normal MOVE SENDED: ' + str(move) + ' mypos: ' + str(self.mypos.x) + ', ' + str(self.mypos.y))
                            else:
                                move = b'left'
                                print('NO MOVE: Death')
                        self.socket.send(b'move|' + move + b'\n')
                        self.others_possible_next_move = []
                    elif m.startswith(b'lose') or m.startswith (b'win'):
                        self.alive = False
                        print('Game Over')
                    elif m.startswith(b'win'):
                        print('I won')
                    elif m.startswith(b'die'):
                        die = m.split(b'|')
                        for r in die[1:]:
                            self.remove(r)
                    elif m.startswith(b'player'):
                        self.addPlayer()
                    elif m.startswith(b'limit'):
                        limit = m.split(b'|')
                        self.limit = Limit(Position(int(limit[1]), int(limit[2])), Position(int(limit[3]), int(limit[4])))
                        print('limit')
                        print(self.limit)
                    else:
                        print('received invalid message')
                        print(m)

    def addPlayer(self):
        self.numberOfPlayers += 1
        self.covered_spaces_by.append([])
                        
snek = Snek()
