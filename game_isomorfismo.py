import pygame
import networkx as nx
import random
import math
import time

# Settings
WIDTH, HEIGHT = 900, 600
NODE_RADIUS = 15
FPS = 60
TOLERANCE = 30  # pixels within which a node snaps and fixes

# Colors
WHITE = (255, 255, 255)
BLUE = (100, 149, 237)
RED = (255, 99, 71)
GREEN = (34, 139, 34)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)
YELLOW = (255, 215, 0)
LIGHT_GRAY = (220, 220, 220)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Graph Isomorphism Puzzle")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)

def generate_graph(n):
    """Generate a random connected graph with n nodes and ~n edges."""
    g = nx.gnm_random_graph(n, n + 1)
    while not nx.is_connected(g):
        g = nx.gnm_random_graph(n, n + 1)
    return g

def layout_circle(nodes, cx, cy, radius):
    """Place nodes evenly on a circle centered at (cx, cy)."""
    pos = {}
    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / len(nodes)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        pos[node] = (x, y)
    return pos

def draw_graph(graph, pos):
    """Draw edges in gray and nodes in blue (no labels)."""
    # Draw edges
    for u, v in graph.edges():
        pygame.draw.line(screen, GRAY, pos[u], pos[v], 2)
    # Draw nodes (without labels)
    for node in graph.nodes():
        x, y = pos[node]
        pygame.draw.circle(screen, BLUE, (int(x), int(y)), NODE_RADIUS)


def draw_current_graph(graph, draggable_pos, fixed_set):
    """Draw the user's current arrangement: edges and draggable/fixed nodes (no labels)."""
    # Draw edges
    for u, v in graph.edges():
        x1, y1 = draggable_pos[u]
        x2, y2 = draggable_pos[v]
        pygame.draw.line(screen, GRAY, (x1, y1), (x2, y2), 2)
    # Draw nodes (green if fixed, blue if movable, no labels)
    for node, (x, y) in draggable_pos.items():
        color = GREEN if node in fixed_set else BLUE
        pygame.draw.circle(screen, color, (int(x), int(y)), NODE_RADIUS)

# Next is draw_button function

def draw_button(rect, text, active=False):
    """Draw a rectangular outline button with centered text."""
    color = RED if active else BLACK
    pygame.draw.rect(screen, color, rect, 2)
    surf = font.render(text, True, color)
    r = surf.get_rect(center=rect.center)
    screen.blit(surf, r)

def main():
    running = True
    base_nodes = 5
    level = 1

    while running:
        n = base_nodes + level - 1
        nodes = list(range(n))
        graph = generate_graph(n)
        # Target (left) positions
        target_pos = layout_circle(nodes, WIDTH//4, HEIGHT//2, 120)
        # Drop spots (right circle) as guides
        drop_pos = layout_circle(nodes, 3*WIDTH//4, HEIGHT//2, 120)
        drop_coords = list(drop_pos.values())

        # Initialize draggable node positions (randomized)
        draggable_pos = {}
        for node in nodes:
            x = random.randint(WIDTH//2 + 20, WIDTH - 40)
            y = random.randint(20, HEIGHT - 60)
            draggable_pos[node] = [x, y]
        fixed_set = set()
        dragging = None
        offset_x = offset_y = 0
        start_time = time.time()
        answered = False
        score = 0

        # Buttons
        show_answer_btn = pygame.Rect(WIDTH//2 - 60, HEIGHT - 50, 120, 40)
        next_btn = pygame.Rect(WIDTH//2 + 100, HEIGHT - 50, 160, 40)

        while True:
            screen.fill(WHITE)
            clock.tick(FPS)

            # Draw the target graph on the left
            draw_graph(graph, target_pos)

            # Draw drop spot outlines on the right
            for coord in drop_coords:
                pygame.draw.circle(screen, LIGHT_GRAY, (int(coord[0]), int(coord[1])), NODE_RADIUS+2, 2)

            # Draw the user's current graph on right
            draw_current_graph(graph, draggable_pos, fixed_set)

            # Draw buttons
            draw_button(show_answer_btn, "Show Answer")
            if answered or len(fixed_set) == n:
                draw_button(next_btn, f"Next Level {level+1}")

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    return

                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    # Reset current level
                    break  # break inner loop to restart level

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    # Show Answer
                    if show_answer_btn.collidepoint(mx, my) and not answered:
                        # Snap each node to its RIGHT-side drop spot, not left target
                        for node in nodes:
                            dx, dy = drop_pos[node]
                            draggable_pos[node] = [dx, dy]
                            fixed_set.add(node)
                        answered = True
                        elapsed = int(time.time() - start_time)
                        score = max(0, 1000 - elapsed)

                    # Next Level
                    elif next_btn.collidepoint(mx, my) and (answered or len(fixed_set) == n):
                        level += 1
                        break  # proceed to next level

                    else:
                        # Try to pick a draggable node
                        for node in nodes:
                            if node in fixed_set:
                                continue
                            x, y = draggable_pos[node]
                            if math.hypot(x - mx, y - my) <= NODE_RADIUS:
                                dragging = node
                                offset_x = x - mx
                                offset_y = y - my
                                break

                elif event.type == pygame.MOUSEBUTTONUP:
                    if dragging is not None and dragging not in fixed_set:
                        mx, my = pygame.mouse.get_pos()
                        # Snap to RIGHT drop position if close enough
                        dx, dy = drop_pos[dragging]
                        if math.hypot(mx - dx, my - dy) <= TOLERANCE:
                            draggable_pos[dragging] = [dx, dy]
                            fixed_set.add(dragging)
                        else:
                            # Otherwise leave where released (current draggable_pos)
                            pass
                    dragging = None

                elif event.type == pygame.MOUSEMOTION:
                    if dragging is not None and dragging not in fixed_set:
                        mx, my = event.pos
                        draggable_pos[dragging] = [mx + offset_x, my + offset_y]

            else:
                # No break, continue drawing
                # Check if all nodes fixed
                if len(fixed_set) == n and not answered:
                    answered = True
                    elapsed = int(time.time() - start_time)
                    score = max(0, 1000 - elapsed)
                pygame.display.flip()
                continue
            # Inner loop break: either reset or next level
            break

        # Continue to next iteration for next level or after reset
        if not running:
            break
        # loop continues for new level or reset

    pygame.quit()

if __name__ == "__main__":
    main()
