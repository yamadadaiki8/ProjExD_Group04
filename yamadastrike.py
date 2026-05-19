import math
import os
import random
import sys
import pygame as pg

WIDTH = 450  # ゲームウィンドウの幅
HEIGHT = 800  # ゲームウィンドウの高さ

try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except:
    pass

# --- カラー定義 ---
STAGE_BORDER = (255, 215, 0)
LINE_COLOR = (255, 0, 0)
SS_LINE_COLOR = (255, 215, 0)
HP_TEXT_COLOR = (255, 50, 50)
TEXT_WHITE = (255, 255, 255)
BUTTON_COLOR = (50, 150, 250)
BUTTON_HOVER_COLOR = (80, 180, 255)


class StrikeShotManager:
    """ストライクショット（SS）のデータ、ロジック、専用UIを管理するクラス。

    敵の撃破数をカウントし、規定数に達すると必殺技（SS）の発動可能フラグを立てる。
    また、画面左上に現在のチャージ状況や発動可能テキストを描画する。

    Attributes:
        requirement (int): SS発動に必要な敵の撃破数。
        killed_count (int): 現在のステージにおける敵の累計撃破数。
        is_ready (bool): SSが発動可能な状態かを表すフラグ。
        font (pg.font.Font): SS状況を画面に描画するためのフォントオブジェクト。
    """
    
    def __init__(self, requirement: int = 3) -> None:
        """StrikeShotManagerを初期化する。

        Args:
            requirement (int): SS発動に必要な撃破数。デフォルトは3。
        """
        self.requirement: int = requirement
        self.killed_count: int = 0
        self.is_ready: bool = False
        self.font: pg.font.Font = pg.font.SysFont("msgothic", 24)

    def reset(self) -> None:
        """SSのチャージカウントと発動可能フラグを初期状態にリセットする。

        ゲームオーバー時や、ステージクリアによるゲームリセット時に呼び出される。
        """
        self.killed_count = 0
        self.is_ready = False

    def charge(self) -> None:
        """撃破数を1増加させ、規定数に達していればSSを発動可能状態にする。

        敵のHPが0になり、ステージから削除されたタイミングで呼び出される。
        すでにSSが利用可能な状態（is_ready == True）の場合は何も行わない。
        """
        if not self.is_ready:
            self.killed_count += 1
            if self.killed_count >= self.requirement:
                self.is_ready = True

    def use(self) -> None:
        """SSの消費処理を行い、フラグと撃破カウンターをリセットする。

        プレイヤーがSS発動のためにショットを放った瞬間に呼び出される。
        """
        self.is_ready = False
        self.killed_count = 0

    def draw_status(self, screen: pg.Surface) -> None:
        """画面左上に現在のSSチャージ状況、または発動可能テキストを描画する。

        Args:
            screen (pg.Surface): 描画対象となるPygameのSurface（ウィンドウ画面）。
        """
        if self.is_ready:
            text: pg.Surface = self.font.render("★SS READY! (全員同時発射)", True, STAGE_BORDER)
        else:
            text = self.font.render(f"SSCharge: {self.killed_count}/{self.requirement}", True, TEXT_WHITE)
        screen.blit(text, (25, 25))


class Player:
    """プレイヤーキャラクターの移動や状態を管理するクラス"""
    def __init__(self, x: float, y: float, image: pg.Surface, size: int = 60) -> None:
        self.x: float = x
        self.y: float = y
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.is_moving: bool = False
        self.image: pg.Surface = image
        self.size: int = size

    @property
    def center(self):
        return (int(self.x + self.size // 2), int(self.y + self.size // 2))

    def launch(self, dx: float, dy: float, dist: float) -> None:
        FIXED_SPEED = 45
        self.vx = (dx / dist) * FIXED_SPEED
        self.vy = (dy / dist) * FIXED_SPEED
        self.is_moving = True

    def update_movement(self) -> None:
        if not self.is_moving:
            return

        self.x += self.vx
        if self.x < 10:
            self.x = 10
            self.vx *= -1
        elif self.x > WIDTH - 10 - self.size:
            self.x = WIDTH - 10 - self.size
            self.vx *= -1

        self.y += self.vy
        if self.y < 10:
            self.y = 10
            self.vy *= -1
        elif self.y > 600 - self.size:
            self.y = 600 - self.size
            self.vy *= -1

        self.vx *= 0.985
        self.vy *= 0.985

        if abs(self.vx) < 0.3 and abs(self.vy) < 0.3:
            self.is_moving = False
            self.vx = 0
            self.vy = 0

    def draw(self, screen: pg.Surface) -> None:
        screen.blit(self.image, (int(self.x), int(self.y)))


class Enemy:
    """敵キャラクターのデータと衝突判定を管理するクラス"""
    def __init__(self, x: int, y: int, enemy_type: int, image: pg.Surface, size: int = 70, hp: int = 15) -> None:
        self.x: int = x
        self.y: int = y
        self.type: int = enemy_type
        self.image: pg.Surface = image
        self.size: int = size
        self.hp: int = hp

    def check_collision(self, player: Player) -> bool:
        if (self.x < player.x + player.size and 
            player.x < self.x + self.size and
            self.y < player.y + player.size and 
            player.y < self.y + self.size):
            
            if player.vx > 0 and player.x + player.size - player.vx <= self.x:
                player.x = self.x - player.size
                player.vx *= -0.9
            elif player.vx < 0 and player.x - player.vx >= self.x + self.size:
                player.x = self.x + self.size
                player.vx *= -0.9

            if player.vy > 0 and player.y + player.size - player.vy <= self.y:
                player.y = self.y - player.size
                player.vy *= -0.9
            elif player.vy < 0 and player.y - player.vy >= self.y + self.size:
                player.y = self.y + self.size
                player.vy *= -0.9
                
            self.hp -= 1
            return True
        return False

    def draw(self, screen: pg.Surface, hp_font: pg.font.Font) -> None:
        screen.blit(self.image, (self.x, self.y))
        hp_text = hp_font.render(f"HP: {self.hp}", True, HP_TEXT_COLOR)
        screen.blit(hp_text, (self.x, self.y - 18))


class GameUI:
    """背景、枠、文字などの描画（UI）全般を専門に行うクラス"""
    def __init__(self) -> None:
        self.bg_img: pg.Surface = pg.transform.scale(pg.image.load("haikei1.png").convert_alpha(), (WIDTH, HEIGHT))
        self.ui_bg_img: pg.Surface = pg.transform.scale(pg.image.load("haikei2.png").convert_alpha(), (WIDTH - 30, 185))
        self.start_bg_img: pg.Surface = pg.transform.scale(pg.image.load("haikei1.png").convert_alpha(), (WIDTH, HEIGHT))
        
        self.hp_font: pg.font.Font = pg.font.SysFont(None, 20)
        self.turn_font: pg.font.Font = pg.font.SysFont(None, 40)
        self.result_font: pg.font.Font = pg.font.SysFont(None, 60)
        self.title_font: pg.font.Font = pg.font.SysFont("msgothic", 50)
        self.button_font: pg.font.Font = pg.font.SysFont(None, 40)
        self.sub_font: pg.font.Font = pg.font.SysFont(None, 25)

    def draw_start_screen(self, screen: pg.Surface, button_rect: pg.Rect) -> None:
        screen.blit(self.start_bg_img, (0, 0))
        title_text = self.title_font.render("簡易モンスト", True, STAGE_BORDER)
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        screen.blit(title_text, title_rect)
        
        mouse_pos = pg.mouse.get_pos()
        color = BUTTON_HOVER_COLOR if button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pg.draw.rect(screen, color, button_rect, border_radius=10)
        pg.draw.rect(screen, TEXT_WHITE, button_rect, 3, border_radius=10)
        
        btn_text = self.button_font.render("START", True, TEXT_WHITE)
        btn_text_rect = btn_text.get_rect(center=button_rect.center)
        screen.blit(btn_text, btn_text_rect)

    def draw_base_layer(self, screen: pg.Surface) -> None:
        screen.blit(self.bg_img, (0, 0))
        pg.draw.rect(screen, STAGE_BORDER, (10, 10, WIDTH - 20, HEIGHT - 20), 4)
        screen.blit(self.ui_bg_img, (15, 600))
        pg.draw.line(screen, STAGE_BORDER, (10, 600), (WIDTH - 10, 600), 4)

    def draw_bottom_ui_icons(self, screen: pg.Surface, chara_images: list, current_turn: int, anyone_moving: bool, game_state: str, ss_ready: bool) -> None:
        """画面下のキャラクターアイコン群の描画を行います。
        
        SSが準備できている（ss_ready=True）ときは、手番に関わらずすべてのアイコンを金枠で囲います。
        """
        for i in range(3):
            x = 80 + i * 110
            y = 630
            screen.blit(chara_images[i], (x, y))
            
            if ss_ready and game_state == "PLAY":
                pg.draw.rect(screen, SS_LINE_COLOR, (x - 4, y - 4, 68, 68), 3)
            elif i == current_turn and not anyone_moving and game_state == "PLAY":
                pg.draw.rect(screen, STAGE_BORDER, (x - 4, y - 4, 68, 68), 3)

    def draw_guide_line(self, screen: pg.Surface, start_pos: tuple, end_pos: tuple, is_ss: bool) -> None:
        """引っ張り中のガイド線を描画します。
        
        SS発動時（is_ss=True）は、通常よりも太い金色の線でガイド線を描画します。
        """
        color = SS_LINE_COLOR if is_ss else LINE_COLOR
        pg.draw.line(screen, color, start_pos, end_pos, 4 if is_ss else 3)

    def draw_turn_count(self, screen: pg.Surface, left_turns: int) -> None:
        turn_text = self.turn_font.render(f"TURN: {left_turns}", True, TEXT_WHITE)
        screen.blit(turn_text, (WIDTH - 140, 25))

    def draw_result_screen(self, screen: pg.Surface, game_state: str) -> None:
        if game_state == "PLAY" or game_state == "START":
            return
            
        mask = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        mask.fill((0, 0, 0, 150))
        screen.blit(mask, (0, 0))
        
        if game_state == "GAMEOVER":
            text = self.result_font.render("GAME OVER", True, (255, 0, 0))
        else:
            text = self.result_font.render("STAGE CLEAR!", True, (0, 255, 0))
            
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(text, text_rect)

        sub_text = self.sub_font.render("CLICK ANYWHERE TO RETURN TO TITLE", True, TEXT_WHITE)
        sub_rect = sub_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
        screen.blit(sub_text, sub_rect)


class Game:
    """ゲームの進行、ループ、イベント、ゲーム状態全体を統括するメインクラス"""
    def __init__(self) -> None:
        pg.init()
        self.screen: pg.Surface = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption("超簡易版モンスト(SS標準アノテーション版)")
        self.clock: pg.time.Clock = pg.time.Clock()
        
        self.ui: GameUI = GameUI()
        
        # --- SS管理マネージャーのインスタンス化 ---
        self.ss_manager: StrikeShotManager = StrikeShotManager(requirement=3)
        
        self.start_button_rect: pg.Rect = pg.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 60)
        
        self.chara_images: list = [
            pg.transform.scale(pg.image.load("chara1.jpg").convert_alpha(), (60, 60)),
            pg.transform.scale(pg.image.load("chara2.jpg").convert_alpha(), (60, 60)),
            pg.transform.scale(pg.image.load("chara3.png").convert_alpha(), (60, 60))
        ]
        self.enemy_images: list = [
            pg.transform.scale(pg.image.load("enemy1.png").convert_alpha(), (70, 70)),
            pg.transform.scale(pg.image.load("enemy1.png").convert_alpha(), (70, 70)),
            pg.transform.scale(pg.image.load("enemy1.png").convert_alpha(), (70, 70))
        ]

        self.game_state: str = "START"
        self.running: bool = True
        self.reset_game()

    def reset_game(self) -> None:
        self.players: list = [
            Player(120, 450, self.chara_images[0]),
            Player(195, 480, self.chara_images[1]),
            Player(270, 450, self.chara_images[2])
        ]
        self.enemies: list = []
        self._spawn_enemies()
        
        self.current_turn: int = 0
        self.is_dragging: bool = False
        self.left_turns: int = 9
        
        # --- マネージャーの初期化 ---
        self.ss_manager.reset()

    def _spawn_enemies(self) -> None:
        num_enemies = random.randint(3, 5)
        for _ in range(num_enemies):
            enemy_type = random.randint(0, 2)
            x = random.randint(30, WIDTH - 100)
            y = random.randint(50, 450)
            img = self.enemy_images[enemy_type]
            self.enemies.append(Enemy(x, y, enemy_type, img, hp=5))

    def handle_events(self) -> None:
        mouse_pos: tuple = pg.mouse.get_pos()
        p = self.players[self.current_turn] if self.game_state == "PLAY" else None
        anyone_moving: bool = any(pl.is_moving for pl in self.players)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            
            if self.game_state == "START":
                if event.type == pg.MOUSEBUTTONDOWN:
                    if self.start_button_rect.collidepoint(mouse_pos):
                        self.game_state = "PLAY"
            
            elif self.game_state == "PLAY":
                if event.type == pg.MOUSEBUTTONDOWN and not anyone_moving:
                    # --- SS READY時は、どのキャラクターを触っても選択（引っ張り）可能にする ---
                    if self.ss_manager.is_ready:
                        for idx, pl in enumerate(self.players):
                            if pl.x <= mouse_pos[0] <= pl.x + pl.size and pl.y <= mouse_pos[1] <= pl.y + pl.size:
                                self.current_turn = idx
                                self.is_dragging = True
                                break
                    else:
                        if p and p.x <= mouse_pos[0] <= p.x + p.size and p.y <= mouse_pos[1] <= p.y + p.size:
                            self.is_dragging = True

                if event.type == pg.MOUSEBUTTONUP and self.is_dragging:
                    self.is_dragging = False
                    p_active: Player = self.players[self.current_turn]
                    p_center: tuple = p_active.center
                    dx: float = p_center[0] - mouse_pos[0]
                    dy: float = p_center[1] - mouse_pos[1]
                    dist: float = math.hypot(dx, dy)
                    
                    if dist > 5:
                        # --- SS発動時は全員同時に launch させ、マネージャーを消費(use)状態にする ---
                        if self.ss_manager.is_ready:
                            for pl in self.players:
                                pl.launch(dx, dy, dist)
                            self.ss_manager.use()
                        else:
                            p_active.launch(dx, dy, dist)
                            
                        self.current_turn = (self.current_turn + 1) % 3

            elif self.game_state in ("GAMEOVER", "CLEAR"):
                if event.type == pg.MOUSEBUTTONDOWN:
                    self.reset_game()
                    self.game_state = "START"

    def update(self) -> None:
        if self.game_state != "PLAY":
            return

        was_anyone_moving: bool = any(pl.is_moving for pl in self.players)

        for player in self.players:
            player.update_movement()
            
            if player.is_moving:
                for enemy in list(self.enemies):
                    if enemy.check_collision(player):
                        if enemy.hp <= 0:
                            self.enemies.remove(enemy)
                            # --- 敵を撃破したタイミングでマネージャーをチャージする ---
                            self.ss_manager.charge()

        is_anyone_moving: bool = any(pl.is_moving for pl in self.players)
        if was_anyone_moving and not is_anyone_moving:
            if len(self.enemies) > 0:
                self.left_turns -= 1
                if self.left_turns <= 0:
                    self.game_state = "GAMEOVER"

        if len(self.enemies) == 0:
            self.game_state = "CLEAR"

    def draw(self) -> None:
        if self.game_state == "START":
            self.ui.draw_start_screen(self.screen, self.start_button_rect)
        else:
            self.ui.draw_base_layer(self.screen)
            
            for enemy in self.enemies:
                enemy.draw(self.screen, self.ui.hp_font)
                
            anyone_moving: bool = any(pl.is_moving for pl in self.players)
            
            # --- 引数追加: ss_manager.is_ready を渡し、アイコンの金枠描画を切り替える ---
            self.ui.draw_bottom_ui_icons(
                self.screen, self.chara_images, self.current_turn, anyone_moving, self.game_state, self.ss_manager.is_ready
            )
            
            for player in self.players:
                player.draw(self.screen)
                
            if self.is_dragging and self.game_state == "PLAY":
                p: Player = self.players[self.current_turn]
                # --- 引数追加: ガイド線を金色にするかの判定用フラグを渡す ---
                self.ui.draw_guide_line(self.screen, p.center, pg.mouse.get_pos(), self.ss_manager.is_ready)
                
            self.ui.draw_turn_count(self.screen, self.left_turns)
            
            # --- 追加: SSマネージャー専用のステータス描画メソッドを呼ぶ ---
            self.ss_manager.draw_status(self.screen)
            
            self.ui.draw_result_screen(self.screen, self.game_state)
        
        pg.display.flip()

    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
            
        pg.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()