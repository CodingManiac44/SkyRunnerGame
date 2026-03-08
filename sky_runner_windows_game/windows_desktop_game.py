import random
import tkinter as tk
from dataclasses import dataclass

WIDTH = 900
HEIGHT = 600
PLAYER_SIZE = 36
ENEMY_SIZE = 34
COIN_SIZE = 20
PLAYER_SPEED = 8
INITIAL_LIVES = 3
SPAWN_INTERVAL_MS = 900
GAME_TICK_MS = 16
BACKGROUND = "#111827"
TEXT = "#F9FAFB"
ACCENT = "#22C55E"
DANGER = "#EF4444"
GOLD = "#F59E0B"


@dataclass
class FallingObject:
    kind: str
    x: float
    y: float
    speed: float
    item_id: int


class SkyRunnerGame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Sky Runner - Desktop Game")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BACKGROUND, highlightthickness=0)
        self.canvas.pack()

        self.left_pressed = False
        self.right_pressed = False
        self.running = False
        self.spawn_interval = SPAWN_INTERVAL_MS
        self.tick_job = None
        self.spawn_job = None

        self.player_x = WIDTH / 2
        self.player_y = HEIGHT - 70
        self.player = None
        self.objects: list[FallingObject] = []
        self.score = 0
        self.best_score = 0
        self.level = 1
        self.lives = INITIAL_LIVES

        self.root.bind("<Left>", self.on_key_press)
        self.root.bind("<Right>", self.on_key_press)
        self.root.bind("<KeyRelease-Left>", self.on_key_release)
        self.root.bind("<KeyRelease-Right>", self.on_key_release)
        self.root.bind("<a>", self.on_key_press)
        self.root.bind("<d>", self.on_key_press)
        self.root.bind("<KeyRelease-a>", self.on_key_release)
        self.root.bind("<KeyRelease-d>", self.on_key_release)
        self.root.bind("<space>", self.on_space)
        self.root.bind("<Return>", self.on_space)

        self.draw_start_screen()

    def draw_gradient_stars(self) -> None:
        self.canvas.delete("bg")
        for i in range(0, HEIGHT, 4):
            shade = 17 + int((i / HEIGHT) * 25)
            color = f"#{shade:02x}{shade + 6:02x}{shade + 18:02x}"
            self.canvas.create_rectangle(0, i, WIDTH, i + 4, fill=color, outline="", tags="bg")
        random.seed(42)
        for _ in range(80):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            r = random.randint(1, 2)
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="#E5E7EB", outline="", tags="bg")

    def draw_start_screen(self) -> None:
        self.draw_gradient_stars()
        self.canvas.delete("ui")
        self.canvas.create_text(WIDTH / 2, 130, text="SKY RUNNER", fill=TEXT, font=("Segoe UI", 30, "bold"), tags="ui")
        self.canvas.create_text(
            WIDTH / 2,
            210,
            text="Arrow keys / A-D diye norbe\nLal bol eirao, sonali coin dhoro",
            fill=TEXT,
            font=("Segoe UI", 16),
            tags="ui",
            justify="center",
        )
        self.canvas.create_text(WIDTH / 2, 300, text="Space chaple khela suru", fill=ACCENT, font=("Segoe UI", 20, "bold"), tags="ui")
        self.canvas.create_text(
            WIDTH / 2,
            380,
            text=f"Best Score: {self.best_score}",
            fill=GOLD,
            font=("Segoe UI", 18, "bold"),
            tags="ui",
        )

    def start_game(self) -> None:
        self.running = True
        self.score = 0
        self.level = 1
        self.lives = INITIAL_LIVES
        self.spawn_interval = SPAWN_INTERVAL_MS
        self.objects.clear()
        self.canvas.delete("all")
        self.draw_gradient_stars()
        self.player_x = WIDTH / 2
        self.player = self.draw_player(self.player_x, self.player_y)
        self.update_hud()
        self.schedule_spawn()
        self.game_loop()

    def draw_player(self, x: float, y: float) -> int:
        points = [
            x, y - PLAYER_SIZE,
            x - PLAYER_SIZE, y + PLAYER_SIZE,
            x, y + PLAYER_SIZE / 2,
            x + PLAYER_SIZE, y + PLAYER_SIZE,
        ]
        return self.canvas.create_polygon(points, fill=ACCENT, outline="#DCFCE7", width=2, tags="player")

    def redraw_player(self) -> None:
        self.canvas.delete("player")
        self.player = self.draw_player(self.player_x, self.player_y)

    def update_hud(self) -> None:
        self.canvas.delete("hud")
        self.canvas.create_text(90, 28, text=f"Score: {self.score}", fill=TEXT, font=("Segoe UI", 16, "bold"), tags="hud")
        self.canvas.create_text(260, 28, text=f"Level: {self.level}", fill=TEXT, font=("Segoe UI", 16, "bold"), tags="hud")
        self.canvas.create_text(420, 28, text=f"Lives: {self.lives}", fill=DANGER, font=("Segoe UI", 16, "bold"), tags="hud")
        self.canvas.create_text(790, 28, text=f"Best: {self.best_score}", fill=GOLD, font=("Segoe UI", 16, "bold"), tags="hud")

    def on_key_press(self, event: tk.Event) -> None:
        if event.keysym in ("Left", "a"):
            self.left_pressed = True
        elif event.keysym in ("Right", "d"):
            self.right_pressed = True

    def on_key_release(self, event: tk.Event) -> None:
        if event.keysym in ("Left", "a"):
            self.left_pressed = False
        elif event.keysym in ("Right", "d"):
            self.right_pressed = False

    def on_space(self, _event: tk.Event) -> None:
        if not self.running:
            self.start_game()

    def schedule_spawn(self) -> None:
        if not self.running:
            return
        self.spawn_object()
        self.spawn_job = self.root.after(self.spawn_interval, self.schedule_spawn)

    def spawn_object(self) -> None:
        x = random.randint(40, WIDTH - 40)
        is_coin = random.random() < 0.25
        kind = "coin" if is_coin else "enemy"
        speed = random.uniform(3.5, 6.0) + (self.level - 1) * 0.35
        size = COIN_SIZE if is_coin else ENEMY_SIZE
        color = GOLD if is_coin else DANGER
        item_id = self.canvas.create_oval(x - size, -size, x + size, size, fill=color, outline="", tags="obj")
        self.objects.append(FallingObject(kind=kind, x=x, y=0, speed=speed, item_id=item_id))

    def intersects_player(self, obj: FallingObject) -> bool:
        px1 = self.player_x - PLAYER_SIZE
        py1 = self.player_y - PLAYER_SIZE
        px2 = self.player_x + PLAYER_SIZE
        py2 = self.player_y + PLAYER_SIZE
        size = COIN_SIZE if obj.kind == "coin" else ENEMY_SIZE
        ox1 = obj.x - size
        oy1 = obj.y - size
        ox2 = obj.x + size
        oy2 = obj.y + size
        return not (px2 < ox1 or px1 > ox2 or py2 < oy1 or py1 > oy2)

    def game_loop(self) -> None:
        if not self.running:
            return

        if self.left_pressed:
            self.player_x -= PLAYER_SPEED
        if self.right_pressed:
            self.player_x += PLAYER_SPEED
        self.player_x = max(PLAYER_SIZE + 10, min(WIDTH - PLAYER_SIZE - 10, self.player_x))
        self.redraw_player()

        remaining: list[FallingObject] = []
        for obj in self.objects:
            obj.y += obj.speed
            self.canvas.move(obj.item_id, 0, obj.speed)

            if self.intersects_player(obj):
                self.canvas.delete(obj.item_id)
                if obj.kind == "coin":
                    self.score += 10
                else:
                    self.lives -= 1
                    self.flash_screen()
                continue

            if obj.y > HEIGHT + 50:
                self.canvas.delete(obj.item_id)
                if obj.kind == "enemy":
                    self.score += 1
                continue

            remaining.append(obj)

        self.objects = remaining
        self.level = max(1, self.score // 25 + 1)
        self.spawn_interval = max(250, SPAWN_INTERVAL_MS - (self.level - 1) * 70)
        self.best_score = max(self.best_score, self.score)
        self.update_hud()

        if self.lives <= 0:
            self.game_over()
            return

        self.tick_job = self.root.after(GAME_TICK_MS, self.game_loop)

    def flash_screen(self) -> None:
        overlay = self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#7F1D1D", stipple="gray25", outline="")
        self.root.after(80, lambda: self.canvas.delete(overlay))

    def game_over(self) -> None:
        self.running = False
        if self.tick_job is not None:
            self.root.after_cancel(self.tick_job)
            self.tick_job = None
        if self.spawn_job is not None:
            self.root.after_cancel(self.spawn_job)
            self.spawn_job = None

        self.canvas.create_rectangle(170, 170, WIDTH - 170, HEIGHT - 150, fill="#0F172A", outline="#334155", width=3, tags="over")
        self.canvas.create_text(WIDTH / 2, 240, text="GAME OVER", fill=TEXT, font=("Segoe UI", 28, "bold"), tags="over")
        self.canvas.create_text(WIDTH / 2, 300, text=f"Final Score: {self.score}", fill=GOLD, font=("Segoe UI", 20, "bold"), tags="over")
        self.canvas.create_text(WIDTH / 2, 370, text="Space chaple abar suru hobe", fill=ACCENT, font=("Segoe UI", 18), tags="over")


def main() -> None:
    root = tk.Tk()
    SkyRunnerGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
