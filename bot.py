import pyautogui
import time
import random
import keyboard
import logging
import json
from PIL import ImageGrab, Image
import numpy as np
import cv2
import tkinter as tk
from tkinter import scrolledtext, messagebox

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
                self.health_position = config.get('health_position', [700, 35])
                self.mana_position = config.get('mana_position', [700, 50])
                self.capacity_position = config.get('capacity_position', [900, 600])
                
                # Waypoints
                self.depot_waypoints = config.get('depot_waypoints', [])
                self.bank_waypoints = config.get('bank_waypoints', [])
                self.npc_waypoints = config.get('npc_waypoints', [])
                self.hunt_waypoints = config.get('hunt_waypoints', [])
                
                # Itens
                self.health_potion_name = config.get('health_potion_name', 'strong health potion')
                self.mana_potion_name = config.get('mana_potion_name', 'strong mana potion')
                self.items_to_buy = config.get('items_to_buy', [])
                self.items_to_deposit = config.get('items_to_deposit', [])
                
                # Thresholds
                self.health_threshold = config.get('health_threshold', 50)
                self.mana_threshold = config.get('mana_threshold', 30)
                
                # Validar thresholds
                if not (0 <= self.health_threshold <= 100):
                    raise ValueError("health_threshold deve estar entre 0 e 100")
                if not (0 <= self.mana_threshold <= 100):
                    raise ValueError("mana_threshold deve estar entre 0 e 100")
                
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
        """Encontrar e atacar monstros (simplificado)"""
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

    def move_to_waypoints(self, waypoints):
        """Navegar por uma lista de waypoints"""
        for wp in waypoints:
            if not self.running or self.paused:
                break
            pyautogui.click(wp['x'], wp['y'])
            time.sleep(wp.get('delay', 1.0))

    def go_to_depot(self):
        """Ir ao depot"""
        if not self.depot_waypoints:
            logging.warning("Waypoints do depot não configurados")
            return
        logging.info("Indo ao depot...")
        self.move_to_waypoints(self.depot_waypoints)

    def manage_inventory(self):
        """Depositar itens e dinheiro"""
        self.go_to_depot()
        pyautogui.click(self.depot_waypoints[-1]['x'], self.depot_waypoints[-1]['y'])  # Último waypoint é o depot
        time.sleep(1)
        pyautogui.typewrite("deposit all\nyes")
        time.sleep(1)
        
        if self.bank_waypoints:
            logging.info("Indo ao banco...")
            self.move_to_waypoints(self.bank_waypoints)
            pyautogui.typewrite("hi\ndeposit all\nyes")
            time.sleep(2)
        logging.info("Itens e dinheiro depositados")

    def buy_supplies(self):
        """Comprar potes de vida e mana"""
        if not self.npc_waypoints:
            logging.warning("Waypoints do NPC não configurados")
            return
        logging.info("Indo ao NPC para comprar suprimentos...")
        self.move_to_waypoints(self.npc_waypoints)
        for item in self.items_to_buy:
            pyautogui.typewrite(f"hi\nbuy {item['quantity']} {item['name']}\n")
            time.sleep(1)
        pyautogui.typewrite("bye")
        time.sleep(2)
        logging.info("Suprimentos comprados")

    def return_to_hunt(self):
        """Voltar à área de caça"""
        if not self.hunt_waypoints:
            logging.warning("Waypoints da hunt não configurados")
            return
        logging.info("Retornando à hunt...")
        self.move_to_waypoints(self.hunt_waypoints)

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
                    self.manage_inventory()
                    self.buy_supplies()
                    self.return_to_hunt()
                else:
                    self.move_character()

                self.add_randomness()
                time.sleep(random.uniform(0.2, 0.5))
            except Exception as e:
                logging.error(f"Erro no ciclo principal: {str(e)}")
                time.sleep(1)

class BotInterface:
    def __init__(self, root):
        self.root = root
        self.bot = TibiaBot()
        self.setup_ui()

    def setup_ui(self):
        """Configurar a interface gráfica"""
        self.root.title("Tibia Bot - Interface")
        self.root.geometry("500x400")

        # Botões
        self.start_button = tk.Button(self.root, text="Iniciar", command=self.start_bot)
        self.start_button.pack(pady=10)

        self.pause_button = tk.Button(self.root, text="Pausar", command=self.pause_bot)
        self.pause_button.pack(pady=10)

        self.stop_button = tk.Button(self.root, text="Parar", command=self.stop_bot)
        self.stop_button.pack(pady=10)

        self.calibrate_button = tk.Button(self.root, text="Calibrar Posições", command=self.calibrate_positions)
        self.calibrate_button.pack(pady=10)

        self.status_label = tk.Label(self.root, text="Status: Parado")
        self.status_label.pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=60, height=15)
        self.log_area.pack(pady=10)
        self.log_area.config(state=tk.DISABLED)

        self.redirect_logs()

    def start_bot(self):
        """Iniciar o bot"""
        self.bot.start()
        self.log("Bot iniciado.")
        self.update_status()

    def pause_bot(self):
        """Pausar o bot"""
        self.bot.pause()
        self.log("Bot pausado." if self.bot.paused else "Bot retomado.")
        self.update_status()

    def stop_bot(self):
        """Parar o bot"""
        self.bot.stop()
        self.log("Bot parado.")
        self.update_status()

    def calibrate_positions(self):
        """Permitir ao usuário definir posições"""
        self.log("Clique na posição da vida em 3 segundos...")
        time.sleep(3)
        self.bot.health_position = pyautogui.position()
        self.log(f"Vida configurada em {self.bot.health_position}")

        self.log("Clique na posição da mana em 3 segundos...")
        time.sleep(3)
        self.bot.mana_position = pyautogui.position()
        self.log(f"Mana configurada em {self.bot.mana_position}")

        self.log("Clique na posição da capacidade em 3 segundos...")
        time.sleep(3)
        self.bot.capacity_position = pyautogui.position()
        self.log(f"Capacidade configurada em {self.bot.capacity_position}")

    def update_status(self):
        """Atualizar o status na interface"""
        if self.bot.running:
            status = "Pausado" if self.bot.paused else "Executando"
        else:
            status = "Parado"
        self.status_label.config(text=f"Status: {status}")

    def log(self, message):
        """Exibir logs na interface"""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.config(state=tk.DISABLED)
        self.log_area.yview(tk.END)

    def redirect_logs(self):
        """Redirecionar logs para a interface"""
        class LogHandler(logging.Handler):
            def __init__(self, log_method):
                super().__init__()
                self.log_method = log_method
            def emit(self, record):
                log_entry = self.format(record)
                self.log_method(log_entry)
        log_handler = LogHandler(self.log)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logging.getLogger().addHandler(log_handler)

if __name__ == "__main__":
    print("Bot Tibia - AVISO: O uso de bots viola os termos de serviço do Tibia")
    print("Este script é apenas para fins educacionais")
    root = tk.Tk()
    app = BotInterface(root)
    root.mainloop()