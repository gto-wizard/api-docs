# What FairPlay does

A player who reads a solver during a live hand has an advantage that the rules of
your room do not allow. FairPlay finds the evidence of that.

You send the hands of your room. GTO Wizard holds the record of every solution its
users opened, and when they opened it. FairPlay compares the two. It reports each
solution lookup that fell between the moment a board was dealt and the moment the
hand finished, on that same board.

One match is one line of evidence: a GTO Wizard account opened this exact board
while this hand was live. FairPlay reports the match. It does not decide what the
match means, and it gives no score and no verdict. The judgement stays with you.

## The shape of the work

1. You send a file of finished hands. Each row carries your own hand id, the board,
   the time the board was dealt and the time the hand finished.
2. GTO Wizard reads the file in the background.
3. You ask for the result until it is ready.
4. You download a file of matches. A hand with no match has no row in it.

The work is not immediate. A large file takes time. Nothing is ready when the send
call answers.

## What you need

- A client id and a client secret for your application. Your GTO Wizard
  representative gives you these.
- A monthly record limit, agreed with GTO Wizard. Every call reports how much of it
  you used.

## The two games

FairPlay reads No-Limit Hold'em by default. It also reads 4-card Pot-Limit Omaha,
which you ask for with the `variant` field of the send call. One file holds one
game.
