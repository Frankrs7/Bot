import pyautogui
import time
import random
import keyboard
import logging
import json
from PIL import ImageGrab, Image
import numpy as np
import cv2

# Configurar logging
logging.basicConfig(filename='tibia_bot.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

class TibiaBot:
    def __init__(self, config_file='config.json'):
        self.running = False
        self.paused = False
        self.load_config(config_file)
        self.setup_hotkeys()

    def load_config(self, config_file):
        """Carregar configurações de um arquivo JSON"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                
                # Hotkeys
                self.heal_hotkey = config.get('heal_hotkey', 'f1')
                self.mana_hotkey = config.get('mana_hotkey', 'f2')
                self.attack_hotkey = config.get('attack_hotkey', 'f3')
                
                # Posições
                self.health_position = config.get('health_position', [390, 3314])
                self.mana_position = config.get('mana_position', [800, 3364])
                self.capacity_position = config.get('capacity_position', [1288, 290])
                self.monster_positions = config.get('monster_positions', [[1210, 370]])
                
                # Itens
                self.health_potion_name = config.get('health_potion_name', 'strong health potion')
                self.mana_potion_name = config.get('mana_potion_name', 'strong mana potion')
                
                # Thresholds
                self.health_threshold = config.get('health_threshold', 50)
                self.mana_threshold = config.get('mana_threshold', 30)
                
        except Exception as e:
            logging.error(f"Erro ao carregar configurações: {str(e)}")
            raise

    def setup_hotkeys(self):
        """Configurar hotkeys para controle do bot"""
        keyboard.add_hotkey('esc', self.stop)
        keyboard.add_hotkey('p', self.pause)

    def start(self):
        """Iniciar o bot"""
        if self.running:
            logging.warning("Bot já está em execução")
            return
        self.running = True
        self.paused = False
        logging.info("Bot iniciado")
        print("Bot iniciado. Pressione 'esc' para parar ou 'p' para pausar.")
        try:
            self.main_loop()
        except Exception as e:
            logging.error(f"Erro no loop principal: {str(e)}")
            print(f"Erro: {str(e)}")
        finally:
            self.stop()

    def stop(self):
        """Parar o bot"""
        self.running = False
        self.paused = False
        logging.info("Bot parado")
        print("Bot parado")

    def pause(self):
        """Pausar o bot temporariamente"""
        self.paused = not self.paused
        status = "pausado" if self.paused else "retomado"
        logging.info(f"Bot {status}")
        print(f"Bot {status}")

    def check_health(self):
        """Verificar vida com base na captura da tela"""
        try:
            screenshot = ImageGrab.grab(bbox=(self.health_position[0], self.health_position[1], 
                                         self.health_position[0] + 50, self.health_position[1] + 10))
            img = np.array(screenshot)
            hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
            lower_green = np.array([40, 50, 50])
            upper_green = np.array([80, 255, 255])
            mask = cv2.inRange(hsv, lower_green, upper_green)
            health_percentage = (cv2.countNonZero(mask) / (50 * 10)) * 100
            if health_percentage < self.health_threshold:
                logging.info(f"HP baixo ({health_percentage:.1f}%), curando...")
                keyboard.press_and_release(self.heal_hotkey)
                time.sleep(random.uniform(0.1, 0.3))
            return health_percentage
        except Exception as e:
            logging.error(f"Erro ao verificar vida: {str(e)}")
            return 100

    def check_mana(self):
        """Verificar mana com base na captura da tela"""
        try:
            screenshot = ImageGrab.grab(bbox=(self.mana_position[0], self.mana_position[1], 
                                         self.mana_position[0] + 50, self.mana_position[1] + 10))
            img = np.array(screenshot)
            hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
            lower_blue = np.array([90, 50, 50])
            upper_blue = np.array([130, 255, 255])
            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            mana_percentage = (cv2.countNonZero(mask) / (50 * 10)) * 100
            if mana_percentage < self.mana_threshold:
                logging.info(f"Mana baixa ({mana_percentage:.1f}%), usando poção...")
                keyboard.press_and_release(self.mana_hotkey)
                time.sleep(random.uniform(0.1, 0.3))
            return mana_percentage
        except Exception as e:
            logging.error(f"Erro ao verificar mana: {str(e)}")
            return 100

    def check_inventory(self):
        """Verificar se o inventário está cheio"""
        try:
            screenshot = ImageGrab.grab(bbox=(self.capacity_position[0], self.capacity_position[1], 
                                         self.capacity_position[0] + 20, self.capacity_position[1] + 20))
            img = np.array(screenshot)
            hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
            lower_red = np.array([0, 120, 70])
            upper_red = np.array([10, 255, 255])
            mask = cv2.inRange(hsv, lower_red, upper_red)
            if cv2.countNonZero(mask) > 50:
                logging.info("Inventário cheio detectado")
                return True
            return False
        except Exception as e:
            logging.error(f"Erro ao verificar inventário: {str(e)}")
            return False

    def find_monster(self):
        """Encontrar e atacar monstros"""
        target_pos = random.choice(self.monster_positions)
        logging.info(f"Monstro encontrado em {target_pos}, atacando...")
        pyautogui.click(target_pos[0], target_pos[1])
        time.sleep(random.uniform(0.2, 0.5))
        keyboard.press_and_release(self.attack_hotkey)
        combat_duration = random.uniform(3.0, 8.0)
        start_time = time.time()
        while time.time() - start_time < combat_duration and self.running and not self.paused:
            self.check_health()
            time.sleep(random.uniform(0.5, 1.0))
        return True

    def collect_loot(self):
        """Coletar loot após matar um monstro"""
        logging.info("Coletando loot...")
        for _ in range(random.randint(1, 3)):
            x_offset = random.randint(-20, 20)
            y_offset = random.randint(-20, 20)
            pyautogui.rightClick(self.monster_positions[0][0] + x_offset,
                                self.monster_positions[0][1] + y_offset)
            time.sleep(random.uniform(0.3, 0.7))

    def move_character(self):
        """Mover personagem para explorar"""
        direction = random.choice(['up', 'down', 'left', 'right'])
        key = {'up': 'w', 'down': 's', 'left': 'a', 'right': 'd'}[direction]
        logging.info(f"Movendo para {direction}")
        keyboard.press(key)
        time.sleep(random.uniform(0.5, 2.0))
        keyboard.release(key)

    def add_randomness(self):
        """Adicionar comportamento aleatório"""
        if random.randint(0, 100) < 5:
            logging.info("Realizando ação aleatória...")
            time.sleep(random.uniform(1.0, 3.0))

    def main_loop(self):
        """Loop principal do bot"""
        while self.running:
            try:
                if self.paused:
                    time.sleep(1)
                    continue

                self.check_health()
                self.check_mana()
                monster_found = self.find_monster()
                if monster_found:
                    self.collect_loot()

                if self.check_inventory():
                    logging.info("Inventário cheio. Pare o bot manualmente.")
                    self.stop()

                self.add_randomness()
                time.sleep(random.uniform(0.2, 0.5))
            except Exception as e:
                logging.error(f"Erro no ciclo principal: {str(e)}")
                time.sleep(1)

if __name__ == "__main__":
    print("Bot Tibia - AVISO: O uso de bots viola os termos de serviço do Tibia")
    print("Este script é apenas para fins educacionais")
    bot = TibiaBot()
    bot.start()
