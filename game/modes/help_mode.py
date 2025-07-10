"""
Help Mode - Game rules and instructions
"""


def show_help():
    """Display game rules and help information"""
    print("=" * 60)
    print("DUTCH CABO - RULES AND INSTRUCTIONS")
    print("=" * 60)
    print()
    
    print("OBJECTIVE:")
    print("Get the lowest total score by the end of the game.")
    print()
    
    print("SETUP:")
    print("- Each player starts with 4 cards face down")
    print("- Players peek at their first card only")
    print("- One card is placed face up as the discard pile")
    print()
    
    print("CARD VALUES:")
    print("- Numbers 2-10: Face value")
    print("- Ace (A): 1 point")
    print("- Jack (J): 11 points")
    print("- Queen (Q): 12 points") 
    print("- King (K): 13 points")
    print()
    
    print("SPECIAL CARDS:")
    print("- Jack: Swap with any opponent card")
    print("- Queen: Peek at any card (yours or opponent)")
    print("- King: Normal value (13 points)")
    print()
    
    print("TURN ACTIONS:")
    print("1. Check for matching cards before drawing")
    print("2. Draw a card from deck or discard pile")
    print("3. Choose action:")
    print("   - Discard: Put drawn card on discard pile")
    print("   - Swap: Replace one of your cards")
    print("   - Use ability: If drawn card has special power")
    print("   - Call DUTCH: End the game (risky!)")
    print("4. Check for matching cards after turn")
    print()
    
    print("MATCHING CARDS:")
    print("- If you have cards matching the top discard value,")
    print("  you can discard them to reduce your hand size!")
    print("- This happens before drawing and after your turn")
    print()
    
    print("CALLING DUTCH:")
    print("- End the game immediately")
    print("- If you have the lowest score, you win")
    print("- If not, you get a penalty!")
    print()
    
    print("GAME MODES:")
    print("1. Quick Play: Instant AI vs AI game")
    print("2. Agent vs Agent: Choose AI matchups") 
    print("3. Auto Battle: Multiple games with statistics")
    print("4. AI vs Human: AI plays while you execute moves")
    print("5. Full Setup: Custom player configuration")
    print("6. Real Life GUI: AI vs Human with visual display")
    print("7. Quick Play GUI: AI vs AI with visual display")
    print()
    
    print("CARD INPUT FORMAT (when needed):")
    print("Examples: 2h, 7d, 10c, 9s, ah, jd, qc, ks")
    print("Suits: h=Hearts, d=Diamonds, c=Clubs, s=Spades")
    print()
    
    print("=" * 60)
    input("Press Enter to return to main menu...") 