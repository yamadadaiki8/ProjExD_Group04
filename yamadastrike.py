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
HP_TEXT_COLOR = (255, 50, 50)
TEXT_WHITE = (255, 255, 255)
BUTTON_COLOR = (50, 150, 250)
BUTTON_HOVER_COLOR = (80, 180, 255)
OBSTACLE_COLOR = (120, 120, 120)

class Player:
    """プレイヤーキャラクターの移動や状態を管理するクラス"""
    def __init__(self, x, y, image, size=60):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.is_moving = False
        self.image = image
        self.size = size

    @property
    def center(self):
        """キャラの中心座標を返す"""
        return (int(self.x + self.size // 2), int(self.y + self.size // 2))

    def launch(self, dx, dy, dist):
        """ショットを放つ"""
        FIXED_SPEED = 45
        self.vx = (dx / dist) * FIXED_SPEED
        self.vy = (dy / dist) * FIXED_SPEED
        self.is_moving = True

    def update_movement(self):
        """移動と壁バウンド、自然減速の処理"""
        if not self.is_moving:
            return

        # X方向の移動と壁バウンド
        self.x += self.vx
        if self.x < 10:
            self.x = 10
            self.vx *= -1
        elif self.x > WIDTH - 10 - self.size:
            self.x = WIDTH - 10 - self.size
            self.vx *= -1

        # Y方向の移動と壁バウンド
        self.y += self.vy
        if self.y < 10:
            self.y = 10
            self.vy *= -1
        elif self.y > 600 - self.size:
            self.y = 600 - self.size
            self.vy *= -1

        # 自然減速
        self.vx *= 0.985
        self.vy *= 0.985

        # 停止判定
        if abs(self.vx) < 0.3 and abs(self.vy) < 0.3:
            self.is_moving = False
            self.vx = 0
            self.vy = 0

    def draw(self, screen):
        """画面に自身を描画"""
        screen.blit(self.image, (int(self.x), int(self.y)))


class Enemy:
    """敵キャラクターのデータと衝突判定を管理するクラス"""
    def __init__(self, x, y, enemy_type, image, size=70, hp=15):
        self.x = x
        self.y = y
        self.type = enemy_type
        self.image = image
        self.size = size
        self.hp = hp

    def check_collision(self, player):
        """プレイヤーとの矩形衝突判定。衝突時は位置を押し戻してTrueを返す"""
        if (self.x < player.x + player.size and 
            player.x < self.x + self.size and
            self.y < player.y + player.size and 
            player.y < self.y + self.size):
            
            # X方向の衝突応答
            if player.vx > 0 and player.x + player.size - player.vx <= self.x:
                player.x = self.x - player.size
                player.vx *= -0.9
            elif player.vx < 0 and player.x - player.vx >= self.x + self.size:
                player.x = self.x + self.size
                player.vx *= -0.9

            # Y方向の衝突応答
            if player.vy > 0 and player.y + player.size - player.vy <= self.y:
                player.y = self.y - player.size
                player.vy *= -0.9
            elif player.vy < 0 and player.y - player.vy >= self.y + self.size:
                player.y = self.y + self.size
                player.vy *= -0.9
                
            self.hp -= 1
            return True
        return False

    def draw(self, screen, hp_font):
        """敵とHPの描画"""
        screen.blit(self.image, (self.x, self.y))
        hp_text = hp_font.render(f"HP: {self.hp}", True, HP_TEXT_COLOR)
        screen.blit(hp_text, (self.x, self.y - 18))


class Obstacle:
    """
    プレイヤーの行く手を阻む障害物クラス（破壊は不可）
    x (float): 障害物の左上X座標
    y (float): 障害物の左上Y座標
    size (int): 障害物の一辺の長さ（正方形）
    """
    def __init__(self, x, y, size=60):
        self.x = x
        self.y = y
        self.size = size

    def check_collision(self, player):
        """
        プレイヤーとの衝突判定。敵の処理をベースにHP減少だけを除外
        プレイヤーキャラクターとの衝突判定を行い、
        衝突時にはプレイヤーの位置の押し戻しと速度の反転（バウンド）処理を行う
        この障害物は破壊不可
        衝突した場合は True、衝突していない場合は False
        """
        if (self.x < player.x + player.size and 
            player.x < self.x + self.size and
            self.y < player.y + player.size and 
            player.y < self.y + self.size):
            
            # X方向の衝突応答
            if player.vx > 0 and player.x + player.size - player.vx <= self.x:
                player.x = self.x - player.size
                player.vx *= -0.9
            elif player.vx < 0 and player.x - player.vx >= self.x + self.size:
                player.x = self.x + self.size
                player.vx *= -0.9

            # Y方向の衝突応答
            if player.vy > 0 and player.y + player.size - player.vy <= self.y:
                player.y = self.y - player.size
                player.vy *= -0.9
            elif player.vy < 0 and player.y - player.vy >= self.y + self.size:
                player.y = self.y + self.size
                player.vy *= -0.9
                
            return True
        return False

    def draw(self, screen):
        """障害物の描画（今回はシンプルな四角形として描画。画像にする場合は blit に変更可能）"""
        pg.draw.rect(screen, OBSTACLE_COLOR, (self.x, self.y, self.size, self.size), border_radius=5)
        pg.draw.rect(screen, TEXT_WHITE, (self.x, self.y, self.size, self.size), 2, border_radius=5)


class GameUI:
    """背景、枠、文字などの描画（UI）全般を専門に行うクラス"""
    def __init__(self):
        # 画像の読み込み
        self.bg_img = pg.transform.scale(pg.image.load("haikei1.png").convert_alpha(), (WIDTH, HEIGHT))
        self.ui_bg_img = pg.transform.scale(pg.image.load("haikei2.png").convert_alpha(), (WIDTH - 30, 185))
        self.start_bg_img = pg.transform.scale(pg.image.load("haikei1.png").convert_alpha(), (WIDTH, HEIGHT))
        
        # フォントの設定
        self.hp_font = pg.font.SysFont(None, 20)
        self.turn_font = pg.font.SysFont(None, 40)
        self.result_font = pg.font.SysFont(None, 60)
        self.title_font = pg.font.SysFont("msgothic", 50)
        self.button_font = pg.font.SysFont(None, 40)
        self.sub_font = pg.font.SysFont(None, 25)

    def draw_start_screen(self, screen, button_rect):
        """スタート画面の描画"""
        screen.blit(self.start_bg_img, (0, 0))
        
        title_text = self.title_font.render("ヤマダストライク", True, STAGE_BORDER)
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        screen.blit(title_text, title_rect)
        
        mouse_pos = pg.mouse.get_pos()
        color = BUTTON_HOVER_COLOR if button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pg.draw.rect(screen, color, button_rect, border_radius=10)
        pg.draw.rect(screen, TEXT_WHITE, button_rect, 3, border_radius=10)
        
        btn_text = self.button_font.render("START", True, TEXT_WHITE)
        btn_text_rect = btn_text.get_rect(center=button_rect.center)
        screen.blit(btn_text, btn_text_rect)

    def draw_base_layer(self, screen):
        """ステージの背景、枠、下部UI背景の基本描画"""
        screen.blit(self.bg_img, (0, 0))
        pg.draw.rect(screen, STAGE_BORDER, (10, 10, WIDTH - 20, HEIGHT - 20), 4)
        screen.blit(self.ui_bg_img, (15, 600))
        pg.draw.line(screen, STAGE_BORDER, (10, 600), (WIDTH - 10, 600), 4)

    def draw_bottom_ui_icons(self, screen, chara_images, current_turn, anyone_moving, game_state):
        """画面下のキャラクターアイコン群の描画"""
        for i in range(3):
            x = 80 + i * 110
            y = 630
            screen.blit(chara_images[i], (x, y))
            if i == current_turn and not anyone_moving and game_state == "PLAY":
                pg.draw.rect(screen, STAGE_BORDER, (x - 4, y - 4, 68, 68), 3)

    def draw_guide_line(self, screen, start_pos, end_pos):
        """引っ張り中の赤いガイド線を描画"""
        pg.draw.line(screen, LINE_COLOR, start_pos, end_pos, 3)

    def draw_turn_count(self, screen, left_turns):
        """右上に残りターン数を描画"""
        turn_text = self.turn_font.render(f"TURN: {left_turns}", True, TEXT_WHITE)
        # 座標を右下(HEIGHT - 50)から右上(25)に変更
        screen.blit(turn_text, (WIDTH - 140, 25))

    def draw_result_screen(self, screen, game_state):
        """ゲームオーバーまたはクリア時の半透明マスクとテキスト描画"""
        if game_state == "PLAY" or game_state == "START":
            return
            
        mask = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        mask.fill((0, 0, 0, 150))
        screen.blit(mask, (0, 0))
        
        if game_state == "GAMEOVER":
            text = self.result_font.render("GAME OVER", True, (255, 0, 0))
        else: # CLEAR
            text = self.result_font.render("STAGE CLEAR!", True, (0, 255, 0))
            
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(text, text_rect)

        sub_text = self.sub_font.render("CLICK ANYWHERE TO RETURN TO TITLE", True, TEXT_WHITE)
        sub_rect = sub_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
        screen.blit(sub_text, sub_rect)


class Game:
    """ゲームの進行、ループ、イベント、ゲーム状態全体を統括するメインクラス"""
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption("超簡易版モンスト(Class版)")
        self.clock = pg.time.Clock()
        
        self.ui = GameUI()
        self.start_button_rect = pg.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 60)
        
        # キャラクター画像の準備
        self.chara_images = [
            pg.transform.scale(pg.image.load("chara1.jpg").convert_alpha(), (60, 60)),
            pg.transform.scale(pg.image.load("chara2.jpg").convert_alpha(), (60, 60)),
            pg.transform.scale(pg.image.load("chara3.png").convert_alpha(), (60, 60))
        ]
        self.enemy_images = [
            pg.transform.scale(pg.image.load("enemy1.png").convert_alpha(), (70, 70)),
            pg.transform.scale(pg.image.load("enemy1.png").convert_alpha(), (70, 70)),
            pg.transform.scale(pg.image.load("enemy1.png").convert_alpha(), (70, 70))
        ]

        self.game_state = "START"
        self.running = True
        self.reset_game()

    def reset_game(self):
        """ゲームを最初からの状態にリセットする"""
        self.players = [
            Player(120, 450, self.chara_images[0]),
            Player(195, 480, self.chara_images[1]),
            Player(270, 450, self.chara_images[2])
        ]
        self.enemies = []
        self._spawn_enemies()
        self.obstacles = []
        self.turn_counter = 0
        self.current_turn = 0
        self.is_dragging = False
        self.left_turns = 9

    def _spawn_enemies(self):
        """敵をランダムに生成してリストに追加（内部用メソッド）"""
        num_enemies = random.randint(2, 3)
        for _ in range(num_enemies):
            enemy_type = random.randint(0, 2)
            x = random.randint(30, WIDTH - 100)
            y = random.randint(50, 450)
            img = self.enemy_images[enemy_type]
            self.enemies.append(Enemy(x, y, enemy_type, img))

    def _spawn_obstacle(self):
        """ランダムな位置に障害物を1つ生成する"""
        x = random.randint(30, WIDTH - 80)
        y = random.randint(50, 450)
        self.obstacles.append(Obstacle(x, y))

    def handle_events(self):
        """マウス操作などのイベント受付処理"""
        mouse_pos = pg.mouse.get_pos()
        
        p = self.players[self.current_turn] if self.game_state == "PLAY" else None
        anyone_moving = any(pl.is_moving for pl in self.players)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            
            # --- スタート画面時のイベント処理 ---
            if self.game_state == "START":
                if event.type == pg.MOUSEBUTTONDOWN:
                    if self.start_button_rect.collidepoint(mouse_pos):
                        self.game_state = "PLAY"
            
            # --- プレイ中のイベント処理 ---
            elif self.game_state == "PLAY":
                # 引っ張り開始判定
                if event.type == pg.MOUSEBUTTONDOWN and not anyone_moving:
                    if p.x <= mouse_pos[0] <= p.x + p.size and p.y <= mouse_pos[1] <= p.y + p.size:
                        self.is_dragging = True

                # ショット発射
                if event.type == pg.MOUSEBUTTONUP and self.is_dragging:
                    self.is_dragging = False
                    p_center = p.center
                    dx = p_center[0] - mouse_pos[0]
                    dy = p_center[1] - mouse_pos[1]
                    dist = math.hypot(dx, dy)
                    
                    if dist > 5:
                        p.launch(dx, dy, dist)
                        self.current_turn = (self.current_turn + 1) % 3

            # --- ゲームオーバー / クリア時のイベント処理 ---
            elif self.game_state in ("GAMEOVER", "CLEAR"):
                if event.type == pg.MOUSEBUTTONDOWN:
                    self.reset_game()
                    self.game_state = "START"

    def update(self):
        """移動、衝突判定、勝敗条件などのゲームロジック更新"""
        if self.game_state != "PLAY":
            return

        # 全プレイヤーの移動更新と敵との衝突判定
        for player in self.players:
            was_moving = player.is_moving
            player.update_movement()
            
            # 移動中なら敵との当たり判定をチェック
            if player.is_moving:
                for enemy in list(self.enemies):
                    if enemy.check_collision(player):
                        if enemy.hp <= 0:
                            self.enemies.remove(enemy)
                for obstacle in self.obstacles:
                    obstacle.check_collision(player)

            # 「このフレームでちょうど止まった」瞬間の判定
            if was_moving and not player.is_moving:
                if len(self.enemies) > 0:
                    self.left_turns -= 1
                    self.turn_counter += 1
                    if self.turn_counter >= 3:
                        self._spawn_obstacle()
                        self.turn_counter = 0 # カウンターをリセット
                
                    if self.left_turns <= 0:
                        self.game_state = "GAMEOVER"

        # クリア判定（常に敵が0匹かをチェック）
        if len(self.enemies) == 0:
            self.game_state = "CLEAR"

    def draw(self):
        """画面の描画処理をまとめて実行"""
        if self.game_state == "START":
            self.ui.draw_start_screen(self.screen, self.start_button_rect)
        else:
            self.ui.draw_base_layer(self.screen)
            
            for enemy in self.enemies:
                enemy.draw(self.screen, self.ui.hp_font)
            
            for obstacle in self.obstacles:
                obstacle.draw(self.screen)

            anyone_moving = any(pl.is_moving for pl in self.players)
            self.ui.draw_bottom_ui_icons(
                self.screen, self.chara_images, self.current_turn, anyone_moving, self.game_state
            )
            
            for player in self.players:
                player.draw(self.screen)
                
            if self.is_dragging and self.game_state == "PLAY":
                p = self.players[self.current_turn]
                self.ui.draw_guide_line(self.screen, p.center, pg.mouse.get_pos())
                
            self.ui.draw_turn_count(self.screen, self.left_turns)
            self.ui.draw_result_screen(self.screen, self.game_state)
        
        pg.display.flip()

    def run(self):
        """メインループの実行"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
            
        pg.quit()
        sys.exit()


# --- ゲームの起動 ---
if __name__ == "__main__":
    game = Game()
    game.run()