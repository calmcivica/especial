#!/usr/bin/env python3
"""
Patch script to add gamification features to the Especialidades app.
This script will apply gamification to the pregunta function in helper.py.
"""

import os
import re
import fileinput
import sys

# Path to the helper.py file
HELPER_PATH = "helper.py"

def apply_patch():
    """Apply the gamification patch to the codebase."""
    
    # 1. Find the location in pregunta function where we need to patch
    pregunta_function_start = False
    patch_location = None
    
    with open(HELPER_PATH, 'r') as file:
        lines = file.readlines()
        
    for i, line in enumerate(lines):
        if 'def pregunta(' in line:
            pregunta_function_start = True
        
        if pregunta_function_start and 'cursor.execute(' in line and 'INSERT INTO [esnowflake].[dbo].Fact_Answers' in lines[i+1]:
            patch_location = i - 2  # Get to the try block start
            break
    
    if patch_location is None:
        print("Could not find location to patch in helper.py")
        return False
    
    # 2. Create the patched version of the file
    new_lines = lines.copy()
    
    # Replace the existing insert block with stored procedure call and gamification
    patch_code = """                        try:
                            is_correct_int = 1 if is_correct else 0
                            is_answered_int = 1 if is_answered else 0
                            
                            # Use direct query for now, will migrate to stored procedure once created
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO [esnowflake].[dbo].Fact_Answers (question_id, user_nickname, type, exam_id, is_correct, is_answered, ANSWER_TIMESTAMP) VALUES (?, ?, ?, NULL, ?, ?, CURRENT_TIMESTAMP)",
                                (n, user, mode, is_correct_int, is_answered_int)
                            )
                            conn.commit()
                            
                            # Award XP for correct answers
                            if is_correct and 'add_experience' in globals():
                                add_experience(conn, user, 5, "Correct answer in practice", False)
                                
                                # Check if this is the first correct answer (for achievement)
                                count_query = "SELECT COUNT(*) FROM [esnowflake].[dbo].Fact_Answers WHERE user_nickname = ? AND is_correct = 1"
                                correct_count = cursor.execute(count_query, (user,)).fetchone()[0]
                                
                                # If this is the first correct answer, we would award achievement here
                                # This requires importing gamification which creates circular imports
                                # Will be handled through stored procedures instead
                        except Exception as e:
                            logger.error(f"Error recording answer: {str(e)}", exc_info=True)
"""
    
    # Find the end of the try block
    try_end = patch_location
    while "except" not in new_lines[try_end]:
        try_end += 1
    
    # Replace the entire try block
    new_lines[patch_location:try_end] = patch_code.splitlines(True)
    
    # 3. Write the patched file
    with open(HELPER_PATH, 'w') as file:
        file.writelines(new_lines)
    
    print("Successfully patched helper.py to add gamification features to pregunta function")
    return True

if __name__ == "__main__":
    # Change to the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    if apply_patch():
        print("Patch applied successfully")
    else:
        print("Failed to apply patch")
        sys.exit(1)