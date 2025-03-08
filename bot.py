import time
import threading
import keyboard
import cv2
import numpy as np
import pyautogui
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageGrab

class TibiaLuxBot:
    def __init__(self):
        self.running = False
        self.healing_active = False
        self.looting_active = False
        self.attacking_active = False
        self.cavebot_active = False
        
        # Configurações gerais
        self.heal_hp_threshold = 70  # Cura quando HP < 70%
        self.mana_threshold = 50     # Usa mana potion quando mana < 50%
        self.attack_interval = 2.0   # Intervalo entre ataques em segundos
        self.scan_interval = 0.3     # Intervalo entre verificações em segundos
        
        # Teclas e hotkeys
        self.hp_potion_key = 'f1'
        self.mana_potion_key = 'f2'
        self.attack_spell_key = 'f3'
        self.heal_spell_key = 'f4'
        self.toggle_key = 'f12'      # Liga/desliga o bot
        
        # Lista de monstros para atacar (por ordem de prioridade)
        self.target_monsters = [
            {"name": "Dragon", "priority": 1},
            {"name": "Dragon Lord", "priority": 2},
            {"name": "Demon", "priority": 3},
            {"name": "Giant Spider", "priority": 4}
        ]
        
        # Waypoints para CaveBot (coordenadas x, y)
        self.waypoints = [
            (100, 100),
            (150, 200),
            (200, 250),
            (250, 200),
            (200, 100)
        ]
        
        # Inicializa interface gráfica
        self.create_gui()
        
        # Inicializa thread principal do bot
        self.bot_thread = None
    
    def create_gui(self):
        # Cria janela principal
        self.root = tk.Tk()
        self.root.title("TibiaLux Inspired Bot")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        # Estilo
        style = ttk.Style()
        style.configure("TButton", padding=5, relief="flat", background="#333")
        style.configure("TCheckbutton", background="#f0f0f0")
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="TibiaLux Bot", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Status
        self.status_var = tk.StringVar(value="Bot: Inativo")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Arial", 12))
        status_label.pack(pady=5)
        
        # Frame de configurações
        config_frame = ttk.LabelFrame(main_frame, text="Configurações", padding=10)
        config_frame.pack(fill=tk.X, pady=10)
        
        # Healing
        ttk.Label(config_frame, text="HP Threshold:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.hp_scale = ttk.Scale(config_frame, from_=10, to=90, orient=tk.HORIZONTAL, length=200,
                                 value=self.heal_hp_threshold)
        self.hp_scale.grid(row=0, column=1, pady=5)
        self.hp_value = ttk.Label(config_frame, text=f"{self.heal_hp_threshold}%")
        self.hp_value.grid(row=0, column=2, padx=5)
        
        # Mana
        ttk.Label(config_frame, text="Mana Threshold:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.mana_scale = ttk.Scale(config_frame, from_=10, to=90, orient=tk.HORIZONTAL, length=200,
                                   value=self.mana_threshold)
        self.mana_scale.grid(row=1, column=1, pady=5)
        self.mana_value = ttk.Label(config_frame, text=f"{self.mana_threshold}%")
        self.mana_value.grid(row=1, column=2, padx=5)
        
        # Módulos
        modules_frame = ttk.LabelFrame(main_frame, text="Módulos", padding=10)
        modules_frame.pack(fill=tk.X, pady=10)
        
        # Checkboxes para módulos
        self.healing_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(modules_frame, text="Auto Healing", variable=self.healing_var).pack(anchor=tk.W, pady=2)
        
        self.attack_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(modules_frame, text="Auto Attack", variable=self.attack_var).pack(anchor=tk.W, pady=2)
        
        self.loot_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(modules_frame, text="Auto Loot", variable=self.loot_var).pack(anchor=tk.W, pady=2)
        
        self.cavebot_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(modules_frame, text="CaveBot", variable=self.cavebot_var).pack(anchor=tk.W, pady=2)
        
        # Lista de monstros
        monsters_frame = ttk.LabelFrame(main_frame, text="Monstros Alvo", padding=10)
        monsters_frame.pack(fill=tk.X, pady=10)
        
        # Lista com checkbox para cada monstro
        for monster in self.target_monsters:
            monster["var"] = tk.BooleanVar(value=True)
            ttk.Checkbutton(monsters_frame, text=monster["name"], variable=monster["var"]).pack(anchor=tk.W)
        
        # Botões
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        start_button = ttk.Button(buttons_frame, text="Iniciar", command=self.start_bot)
        start_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        stop_button = ttk.Button(buttons_frame, text="Parar", command=self.stop_bot)
        stop_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Área de logs
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = tk.Text(log_frame, height=10, width=50)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Atualizar valores dos sliders
        self.hp_scale.configure(command=self.update_hp_value)
        self.mana_scale.configure(command=self.update_mana_value)
        
        # Configurar encerramento adequado
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def update_hp_value(self, value):
        value = int(float(value))
        self.heal_hp_threshold = value
        self.hp_value.configure(text=f"{value}%")
        
    def update_mana_value(self, value):
        value = int(float(value))
        self.mana_threshold = value
        self.mana_value.configure(text=f"{value}%")
    
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def start_bot(self):
        if not self.running:
            self.running = True
            self.status_var.set("Bot: Ativo")
            self.healing_active = self.healing_var.get()
            self.attacking_active = self.attack_var.get()
            self.looting_active = self.loot_var.get()
            self.cavebot_active = self.cavebot_var.get()
            
            self.log("Bot iniciado")
            self.bot_thread = threading.Thread(target=self.bot_main_loop)
            self.bot_thread.daemon = True
            self.bot_thread.start()
    
    def stop_bot(self):
        if self.running:
            self.running = False
            self.status_var.set("Bot: Inativo")
            self.log("Bot parado")
    
    def bot_main_loop(self):
        self.log("Thread principal iniciada")
        
        last_attack_time = 0
        current_waypoint = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Módulo de healing
                if self.healing_active:
                    self.check_health()
                
                # Módulo de ataque
                if self.attacking_active and current_time - last_attack_time > self.attack_interval:
                    if self.attack_target():
                        last_attack_time = current_time
                
                # Módulo de looting
                if self.looting_active:
                    self.check_for_loot()
                
                # Módulo de CaveBot
                if self.cavebot_active and len(self.waypoints) > 0:
                    current_waypoint = self.move_to_waypoint(current_waypoint)
                
                # Intervalo entre verificações
                time.sleep(self.scan_interval)
                
            except Exception as e:
                self.log(f"Erro: {str(e)}")
                time.sleep(1)
    
    def check_health(self):
        # Simulação de leitura de HP/Mana (na implementação real, usaria reconhecimento de imagem)
        # Para um bot real, você precisaria capturar a tela e identificar a barra de HP/mana
        
        # Simulando HP baixo a cada ~10 segundos para demonstração
        if time.time() % 10 < 1:
            self.log("HP Baixo! Usando poção de vida")
            keyboard.press_and_release(self.hp_potion_key)
        
        # Simulando Mana baixa a cada ~15 segundos para demonstração
        if time.time() % 15 < 1:
            self.log("Mana Baixa! Usando poção de mana")
            keyboard.press_and_release(self.mana_potion_key)
    
    def attack_target(self):
        # Simulação de detecção de monstro (no bot real, usaria reconhecimento de imagem)
        # Ataca um monstro aleatório da lista para demonstração
        
        active_monsters = [m for m in self.target_monsters if m["var"].get()]
        if not active_monsters:
            return False
        
        # Simulação de encontrar monstro (frequência aleatória)
        if np.random.random() < 0.3:  # 30% de chance de "encontrar" um monstro
            monster = np.random.choice(active_monsters)
            self.log(f"Atacando {monster['name']}")
            keyboard.press_and_release(self.attack_spell_key)
            return True
        
        return False
    
    def check_for_loot(self):
        # Simulação de looting
        # No bot real, identificaria corpos de monstros e clicaria para lootear
        
        # Simulação de loot a cada ~8 segundos
        if time.time() % 8 < 0.3:
            self.log("Coletando loot")
            # Simulação de movimento do mouse para lootear
            current_pos = pyautogui.position()
            pyautogui.moveTo(current_pos[0] + 50, current_pos[1] + 50, duration=0.2)
            pyautogui.click(button='right')
            time.sleep(0.1)
            pyautogui.moveTo(current_pos, duration=0.2)
    
    def move_to_waypoint(self, current_idx):
        # Simulação de movimento entre waypoints
        # No bot real, moveria o personagem clicando nas coordenadas
        
        # A cada ~5 segundos, move para o próximo waypoint
        if time.time() % 5 < 0.3:
            next_idx = (current_idx + 1) % len(self.waypoints)
            wp = self.waypoints[next_idx]
            self.log(f"Movendo para waypoint {next_idx}: ({wp[0]}, {wp[1]})")
            return next_idx
        
        return current_idx
    
    def on_close(self):
        self.stop_bot()
        self.root.destroy()
    
    def run(self):
        # Configurar hotkey global para ligar/desligar o bot
        keyboard.add_hotkey(self.toggle_key, self.toggle_bot)
        
        # Iniciar loop da interface gráfica
        self.root.mainloop()
    
    def toggle_bot(self):
        if self.running:
            self.stop_bot()
        else:
            self.start_bot()

# Iniciar o bot
if __name__ == "__main__":
    bot = TibiaLuxBot()
    bot.run()
