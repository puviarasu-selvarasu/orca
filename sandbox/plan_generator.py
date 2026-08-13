import json
import re
from chat.llm_wrapper import get_llm
import logging

logger = logging.getLogger(__name__)

PLAN_GENERATION_PROMPT = """You are O.R.C.A.'s build engine. Given a user request, generate a JSON plan to build the software.

The JSON must have this exact structure:
{
    "project_name": "unique_and_meaningful_name",
    "files": [
        {"path": "path/to/file.ext", "content": "full file content here"},
        {"path": "path/to/another/file.ext", "content": "full file content here"}
    ],
    "commands": [
        "command1 to run",
        "command2 to run"
    ]
}

CRITICAL RULES:
- If the user asks for a game (Pygame), the `files` MUST contain a single file `game.py` with the COMPLETE Pygame code. Include `pip install pygame` in commands.
- If the user asks for a web app with "Django" or "Python", generate a Django project with requirements and settings files.
- Output ONLY valid JSON. No explanations, no markdown, no extra text."""

FALLBACK_GAME_CODE = '''import pygame
import sys
import random

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Shooter")
clock = pygame.time.Clock()
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

player = pygame.Rect(SCREEN_WIDTH//2 - 25, SCREEN_HEIGHT - 60, 50, 40)
enemies = []
bullets = []
score = 0
game_over = False
game_started = False
enemy_spawn_counter = 0

def draw_start_screen():
    screen.fill(BLACK)
    font = pygame.font.Font(None, 48)
    title = font.render("Space Shooter", True, WHITE)
    start = pygame.font.Font(None, 32).render("Press SPACE to start", True, WHITE)
    screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//2 - 60))
    screen.blit(start, (SCREEN_WIDTH//2 - start.get_width()//2, SCREEN_HEIGHT//2 + 20))
    pygame.display.flip()

while not game_started:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            game_started = True
    clock.tick(FPS)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_UP and not game_over:
            bullets.append(pygame.Rect(player.x + 20, player.y - 10, 10, 20))

    if not game_over:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.x > 0: player.x -= 5
        if keys[pygame.K_RIGHT] and player.x < SCREEN_WIDTH - player.width: player.x += 5

        enemy_spawn_counter += 1
        if enemy_spawn_counter % 30 == 0:
            enemies.append(pygame.Rect(random.randint(0, SCREEN_WIDTH-30), -30, 30, 30))

        for enemy in enemies[:]:
            enemy.y += 3
            if enemy.y > SCREEN_HEIGHT: enemies.remove(enemy)

        for bullet in bullets[:]:
            bullet.y -= 10
            if bullet.y < 0: bullets.remove(bullet)

        for enemy in enemies[:]:
            for bullet in bullets[:]:
                if enemy.colliderect(bullet):
                    enemies.remove(enemy)
                    bullets.remove(bullet)
                    score += 1
            if player.colliderect(enemy):
                game_over = True

        screen.fill(BLACK)
        pygame.draw.rect(screen, GREEN, player)
        for enemy in enemies: pygame.draw.rect(screen, RED, enemy)
        for bullet in bullets: pygame.draw.rect(screen, WHITE, bullet)
        pygame.display.flip()
        clock.tick(FPS)
'''

def is_placeholder(content):
    placeholders = ["Pygame code here", "Django code here", "Code here", "TODO", "Your code here"]
    return any(p.lower() in content.lower() for p in placeholders) or len(content.strip()) < 20

def generate_plan(user_description: str) -> dict:
    llm = get_llm()
    if llm is None:
        return {"error": "LLM not loaded."}
    
    full_prompt = f"{PLAN_GENERATION_PROMPT}\n\nUser request: {user_description}\n\nJSON plan:"
    response = llm.create_completion(prompt=full_prompt, max_tokens=4096, temperature=0.2, stop=["```"], echo=False)
    raw_output = response['choices'][0]['text'].strip()
    
    json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
    if not json_match:
        return {"error": "Failed to parse JSON."}
    
    plan = json.loads(json_match.group())
    desc_lower = user_description.lower()
    
    for file_item in plan.get('files', []):
        if is_placeholder(file_item.get('content', '')):
            if 'game' in file_item.get('path', '').lower() or 'pygame' in desc_lower:
                file_item['content'] = FALLBACK_GAME_CODE
                
    if not plan.get('files') or any(is_placeholder(f['content']) for f in plan['files']):
        plan['files'] = [{"path": "game.py", "content": FALLBACK_GAME_CODE}]
        plan['commands'] = ["pip install pygame", "python game.py"]
        plan['project_name'] = 'space_shooter'
        
    return plan