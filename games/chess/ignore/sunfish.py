# This is a simple chess AI written in python that I have adapted to my needs
# the original author and file can be found here; https://github.com/thomasahle/sunfish


from __future__ import print_function, division
from collections import OrderedDict, namedtuple
import re, math

TABLE_SIZE = 1e6

# This constant controls how much time we spend on looking for optimal moves.
NODES_SEARCHED = 1e4

# Mate value must be greater than 8*queen + 2*(rook+knight+bishop)
# King value is set to twice this value such that if the opponent is
# 8 queens up, but we got the king, we still exceed MATE_VALUE.
MATE_VALUE = 30000

# evaluation
pst = {
	"P":(
		198,198,198,198,198,198,198,198,
		178,198,198,198,198,198,198,178,
		178,198,198,198,198,198,198,178,
		178,198,208,218,218,208,198,178,
		178,198,218,238,238,218,198,178,
		178,198,208,218,218,208,198,178,
		178,198,198,198,198,198,198,178,
		198,198,198,198,198,198,198,198
	),
	"B":(
		797,824,817,808,808,817,824,797,
		814,841,834,825,825,834,841,814,
		818,845,838,829,829,838,845,818,
		824,851,844,835,835,844,851,824,
		827,854,847,838,838,847,854,827,
		826,853,846,837,837,846,853,826,
		817,844,837,828,828,837,844,817,
		792,819,812,803,803,812,819,792
	),
	"N":(
		627,762,786,798,798,786,762,627,
		763,798,822,834,834,822,798,763,
		817,852,876,888,888,876,852,817,
		797,832,856,868,868,856,832,797,
		799,834,858,870,870,858,834,799,
		758,793,817,829,829,817,793,758,
		739,774,798,810,810,798,774,739,
		683,718,742,754,754,742,718,683
	),
	"R":(
		1258,1263,1268,1272,1272,1268,1263,1258,
		1258,1263,1268,1272,1272,1268,1263,1258,
		1258,1263,1268,1272,1272,1268,1263,1258,
		1258,1263,1268,1272,1272,1268,1263,1258,
		1258,1263,1268,1272,1272,1268,1263,1258,
		1258,1263,1268,1272,1272,1268,1263,1258,
		1258,1263,1268,1272,1272,1268,1263,1258,
		1258,1263,1268,1272,1272,1268,1263,1258
	),
	"Q":(
		2529,2529,2529,2529,2529,2529,2529,2529,
		2529,2529,2529,2529,2529,2529,2529,2529,
		2529,2529,2529,2529,2529,2529,2529,2529,
		2529,2529,2529,2529,2529,2529,2529,2529,
		2529,2529,2529,2529,2529,2529,2529,2529,
		2529,2529,2529,2529,2529,2529,2529,2529,
		2529,2529,2529,2529,2529,2529,2529,2529,
		2529,2529,2529,2529,2529,2529,2529,2529
	),
	"K":(
		60098,60132,60073,60025,60025,60073,60132,60098,
		60119,60153,60094,60046,60046,60094,60153,60119,
		60146,60180,60121,60073,60073,60121,60180,60146,
		60173,60207,60148,60100,60100,60148,60207,60173,
		60196,60230,60171,60123,60123,60171,60230,60196,
		60224,60258,60199,60151,60151,60199,60258,60224,
		60287,60321,60262,60214,60214,60262,60321,60287,
		60298,60332,60273,60225,60225,60273,60332,60298
	)
}

N = 16
S = -16
E = 1
W = -1

logic={
	"b":(N+E,S+E,S+W,N+W),
	"n":(2*N+E,N+2*E,S+2*E,2*S+E,2*S+W,S+2*W,N+2*W,2*N+W),
	"r":(N,E,S,W),
	"k":(N,E,S,W,N+E,S+E,S+W,N+W),
	"p":(N,N+W,N+E)
}

#------------------------
#- helper
def getRank( index ):
	return int(math.floor((index - 1) / 8))

def getFile( index ):
	return  (index - 1) % 8

def getRealIndex( index ):
	return ((index + (index & 7)) >> 1) + 1

def getBitIndex( index ):
	return index + ((index - 1) & ~7) - 1

def getValidIndex( index ):
	return (index & 0x88) == 0

def inRange(val, min, max):
	if val < min: return False
	if val > max: return False
	return True

def isEnemy(ip, tp):
	return inRange(ord(ip), 96, 122) != inRange(ord(tp), 96, 122)

def getPromote(index):
	if getRank(index) == 7:
		return True
	else:
		return False

#------------------------
#- board class
class Position(namedtuple("Position", "board score wc bc")):

	def rotate(self):
		return Position(self.board[::-1].swapcase(), -self.score, self.bc, self.wc)

	def getPiece(self, index):
		#if index - 1 == 0 or index + 1 == 65:
		#	return False
		#else:
			return self.board[index - 1]

	def getPawnMoves(self, index, ownpiece):
		bit  = getBitIndex(index)
		rank = getRank(index)

		side = inRange(ord(ownpiece), 96, 122) and 1 or -1
		cdbl = (side == -1 and rank == 6) or (side == 1 and rank == 1)

		for k, shift in enumerate(logic["p"]):
			nextIndex = bit + shift*side

			if k == 0:
				if getValidIndex(nextIndex):
					nextIndex = getRealIndex(nextIndex)
					nextPiece = self.getPiece(nextIndex)
					if nextPiece == ".":
						yield(index, nextIndex)
						if cdbl:
							nextIndex = nextIndex + 8*side
							nextPiece = self.getPiece(nextIndex)
							if nextPiece == ".":
								yield(index, nextIndex)
			else:
				if getValidIndex(nextIndex):
					nextIndex = getRealIndex(nextIndex)
					nextPiece = self.getPiece(nextIndex)
					if nextPiece != "." and isEnemy(nextPiece, ownpiece):
						yield(index, nextIndex)


	def getKnightMoves(self, index, ownpiece):
		bit = getBitIndex(index)

		for k, shift in enumerate(logic["n"]):
			nextIndex = bit + shift

			if getValidIndex(nextIndex):
				nextIndex = getRealIndex(nextIndex)
				nextPiece = self.getPiece(nextIndex)

				if nextPiece == "." or isEnemy(nextPiece, ownpiece):
					yield(index, nextIndex)


	def getKingMoves(self, index, ownpiece):
		bit = getBitIndex(index)

		for k, shift in enumerate(logic["k"]):
			nextIndex = bit + shift

			if getValidIndex(nextIndex):
				nextIndex = getRealIndex(nextIndex)
				nextPiece = self.getPiece(nextIndex)

				if nextPiece == "." or isEnemy(nextPiece, ownpiece):
					yield(index, nextIndex)

	def getBishopMoves(self, index, ownpiece):
		bit = getBitIndex(index)

		for k, shift in enumerate(logic["b"]):
			nextIndex = bit

			while True:
				nextIndex = nextIndex + shift
				if not getValidIndex(nextIndex):
					break

				realIndex = getRealIndex(nextIndex)
				nextPiece = self.getPiece(realIndex)

				if nextPiece == "." or isEnemy(nextPiece, ownpiece):
					yield(index, realIndex)

					if nextPiece != ".":
						break
				else:
					break

	def getRookMoves(self, index, ownpiece):
		bit = getBitIndex(index)

		for k, shift in enumerate(logic["r"]):
			nextIndex = bit

			while True:
				nextIndex = nextIndex + shift
				if not getValidIndex(nextIndex):
					break

				realIndex = getRealIndex(nextIndex)
				nextPiece = self.getPiece(realIndex)

				if nextPiece == "." or isEnemy(nextPiece, ownpiece):
					yield(index, realIndex)

					if nextPiece != ".":
						break
				else:
					break

	def genMoves(self):
		for index, piece in enumerate(self.board):
			if not piece.isupper(): continue

			if piece == "P":
				moves = self.getPawnMoves(index + 1, piece)
				if moves is not None:
					for move in sorted(moves):
						yield(move)

			if piece == "N":
				moves = self.getKnightMoves(index + 1, piece)
				if moves is not None:
					for move in sorted(moves):
						yield(move)

			if piece == "K":
				moves = self.getKingMoves(index + 1, piece)
				if moves is not None:
					for move in sorted(moves):
						yield(move)

			if piece == "R":
				moves = self.getRookMoves(index + 1, piece)
				if moves is not None:
					for move in sorted(moves):
						yield(move)

			if piece == "B":
				moves = self.getBishopMoves(index + 1, piece)
				if moves is not None:
					for move in sorted(moves):
						yield(move)

			if piece == "Q":
				moves = self.getBishopMoves(index + 1, piece)
				if moves is not None:
					for move in sorted(moves):
						yield(move)
				moves = self.getRookMoves(index + 1, piece)
				if moves is not None:
					for move in sorted(moves):
						yield(move)

	def move(self, move):
		i, j = move

		i = i - 1
		j = j - 1

		p, q = self.board[i], self.board[j]

		put = lambda board, i, p: board[:i] + p + board[i+1:]
		# Copy variables and reset ep and kp
		board = self.board
		score = self.score + self.value(move)
		# Actual move
		board = put(board, j, board[i])
		board = put(board, i, ".")

		if p == "P":
			if getPromote(j):
				board = put(board, j, "Q")

		return Position(board, score, self.wc, self.bc).rotate()

	def value(self, move):
		i, j = move

		i = i - 1
		j = j - 1

		p, q = self.board[i], self.board[j]

		# Actual move
		score = pst[p][j] - pst[p][i]
		# Capture
		if q.islower():
			score += pst[q.upper()][j]
		# Special pawn stuff
		if p == "P":
			if getPromote(j):
				score += pst["Q"][j] - pst["P"][j]

		return score

Entry = namedtuple("Entry", "depth score gamma move")
tp = OrderedDict()


###############################################################################
# Search logic
###############################################################################

nodes = 0
def bound(pos, gamma, depth):
	""" returns s(pos) <= r < gamma    if s(pos) < gamma
		returns s(pos) >= r >= gamma   if s(pos) >= gamma """
	global nodes; nodes += 1

	# Look in the table if we have already searched this position before.
	# We use the table value if it was done with at least as deep a search
	# as ours, and the gamma value is compatible.
	entry = tp.get(pos)
	if entry is not None and entry.depth >= depth and (
			entry.score < entry.gamma and entry.score < gamma or
			entry.score >= entry.gamma and entry.score >= gamma):
		return entry.score

	# Stop searching if we have won/lost.
	if abs(pos.score) >= MATE_VALUE:
		return pos.score

	# Null move. Is also used for stalemate checking
	nullscore = -bound(pos.rotate(), 1-gamma, depth-3) if depth > 0 else pos.score
	#nullscore = -MATE_VALUE*3 if depth > 0 else pos.score
	if nullscore >= gamma:
		return nullscore

	# We generate all possible, pseudo legal moves and order them to provoke
	# cuts. At the next level of the tree we are going to minimize the score.
	# This can be shown equal to maximizing the negative score, with a slightly
	# adjusted gamma value.
	best, bmove = -3*MATE_VALUE, None
	for move in sorted(pos.genMoves(), key=pos.value, reverse=True):
		# We check captures with the value function, as it also contains ep and kp
		if depth <= 0 and pos.value(move) < 150:
			break
		score = -bound(pos.move(move), 1-gamma, depth-1)
		if score > best:
			best = score
			bmove = move
		if score >= gamma:
			break

	# If there are no captures, or just not any good ones, stand pat
	if depth <= 0 and best < nullscore:
		return nullscore
	# Check for stalemate. If best move loses king, but not doing anything
	# would save us. Not at all a perfect check.
	if depth > 0 and best <= -MATE_VALUE is None and nullscore > -MATE_VALUE:
		best = 0

	# We save the found move together with the score, so we can retrieve it in
	# the play loop. We also trim the transposition table in FILO order.
	# We prefer fail-high moves, as they are the ones we can build our pv from.
	if entry is None or depth >= entry.depth and best >= gamma:
		tp[pos] = Entry(depth, best, gamma, bmove)
		if len(tp) > TABLE_SIZE:
			tp.popitem()
	return best


def search(pos, maxn=NODES_SEARCHED):
	""" Iterative deepening MTD-bi search """
	global nodes; nodes = 0

	# We limit the depth to some constant, so we don't get a stack overflow in
	# the end game.
	for depth in range(1, 99):
		# The inner loop is a binary search on the score of the position.
		# Inv: lower <= score <= upper
		# However this may be broken by values from the transposition table,
		# as they don't have the same concept of p(score). Hence we just use
		# 'lower < upper - margin' as the loop condition.
		lower, upper = -3*MATE_VALUE, 3*MATE_VALUE
		while lower < upper - 3:
			gamma = (lower+upper+1)//2
			score = bound(pos, gamma, depth)
			if score >= gamma:
				lower = score
			if score < gamma:
				upper = score

		# print("Searched %d nodes. Depth %d. Score %d(%d/%d)" % (nodes, depth, score, lower, upper))

		# We stop deepening if the global N counter shows we have spent too
		# long, or if we have already won the game.
		if nodes >= maxn or abs(score) >= MATE_VALUE:
			break

	# If the game hasn't finished we can retrieve our move from the
	# transposition table.
	entry = tp.get(pos)
	if entry is not None:
		return entry.move, score
	return None, score

def parseFEN(fen):
	board, color, castling = fen.split()
	board = re.sub('\d', (lambda m: '.'*int(m.group(0))), board)
	board = board.replace("/", "")

	wc = ('Q' in castling, 'K' in castling)
	bc = ('k' in castling, 'q' in castling)

	score = sum(pst[p][i] for i,p in enumerate(board) if p.isupper())
	score -= sum(pst[p.upper()][i] for i,p in enumerate(board) if p.islower())

	pos = Position(board, score, wc, bc)
	return (pos if color == 'w' else pos.rotate(), color)

def getAIMove(fenstr):
	pos, color = parseFEN(fenstr)
	m, _ = search(pos, maxn=400)

	if m is None:
		return "Mate"
	else:
		return  str(65 - m[0]).zfill(2) + str(65 - m[1]).zfill(2) + pos.board[65 - m[1] - 1]


def selfPlay(empty):
	pos, color = parseFEN("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR/ w KQkq")

	mlist = ""

	for d in range(200):
		board = pos.board if d % 2 == 0 else pos.rotate().board
		m, _ = search(pos, maxn=200)

		if m is None:
			break

		if d % 2 == 0:
			mlist = mlist + str(m[0]).zfill(2) + str(m[1]).zfill(2) + pos.board[m[1] - 1]
		else:
			mlist = mlist + str(65 - m[0]).zfill(2) + str(65 - m[1]).zfill(2) + pos.board[65 - m[1] - 1]

		pos = pos.move(m)

	return mlist
