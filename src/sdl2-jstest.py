#!/usr/bin/env python3
"""
sdl-jstest - Joystick Test Program for SDL (Python version)
Traduit du programme C original par Ingo Ruhnke <grumbel@gmail.com>

Ce programme utilise pygame pour tester les manettes et contrôleurs de jeu.
"""

import pygame
import sys
import time
import argparse
import curses
import threading
from typing import Optional
import os
import glob
import struct
import fcntl

VERSION = "2.0.0-python"

def print_bar(pos: int, length: int) -> str:
    """Crée une barre de progression ASCII"""
    bar = "["
    for i in range(length):
        if i == pos:
            bar += "#"
        else:
            bar += " "
    bar += "]"
    return bar

def print_joystick_info(joy_id: int, joystick: pygame.joystick.Joystick):
    """Affiche les informations détaillées d'une manette"""
    print(f"Joystick Name:     '{joystick.get_name()}'")
    print(f"Joystick GUID:     {joystick.get_guid()}")
    print(f"Joystick Number:   {joy_id:2d}")
    print(f"Number of Axes:    {joystick.get_numaxes():2d}")
    print(f"Number of Buttons: {joystick.get_numbuttons():2d}")
    print(f"Number of Hats:    {joystick.get_numhats():2d}")
    print(f"Number of Balls:   {joystick.get_numballs():2d}")
    
    # Vérifier si c'est un contrôleur de jeu
    is_gamecontroller = pygame.joystick.get_count() > joy_id
    print("GameControllerConfig:")
    if not is_gamecontroller:
        print("  missing (see gamecontroller mapping)")
    else:
        print(f"  Name:    '{joystick.get_name()}'")
        print(f"  GUID:    '{joystick.get_guid()}'")
    print()

def list_joysticks():
    """Liste toutes les manettes disponibles"""
    pygame.init()
    pygame.joystick.init()
    
    num_joysticks = pygame.joystick.get_count()
    if num_joysticks == 0:
        print("No joysticks were found")
    else:
        print(f"Found {num_joysticks} joystick(s)\n")
        for joy_id in range(num_joysticks):
            try:
                joystick = pygame.joystick.Joystick(joy_id)
                joystick.init()
                print_joystick_info(joy_id, joystick)
                joystick.quit()
            except pygame.error as e:
                print(f"Unable to open joystick {joy_id}: {e}")

def test_joystick(joy_id: int):
    """Test interactif d'une manette avec affichage curses"""
    pygame.init()
    pygame.joystick.init()
    
    if joy_id >= pygame.joystick.get_count():
        print(f"Error: Joystick {joy_id} not found")
        return
    
    try:
        joystick = pygame.joystick.Joystick(joy_id)
        joystick.init()
    except pygame.error as e:
        print(f"Unable to open joystick {joy_id}: {e}")
        return
    
    # Initialiser curses
    stdscr = curses.initscr()
    try:
        curses.noecho()
        curses.cbreak()
        stdscr.nodelay(True)
        curses.curs_set(0)
        
        num_axes = joystick.get_numaxes()
        num_buttons = joystick.get_numbuttons()
        num_hats = joystick.get_numhats()
        num_balls = joystick.get_numballs()
        
        # Initialiser les valeurs
        axes = [0.0] * num_axes
        buttons = [False] * num_buttons
        hats = [(0, 0)] * num_hats
        balls = [(0, 0)] * num_balls
        
        clock = pygame.time.Clock()
        quit_flag = False
        
        while not quit_flag:
            # Traiter les événements pygame
            pygame.event.pump()
            
            something_new = False
            
            # Lire les axes
            for i in range(num_axes):
                new_value = joystick.get_axis(i)
                if abs(new_value - axes[i]) > 0.01:  # Seuil pour éviter le bruit
                    axes[i] = new_value
                    something_new = True
            
            # Lire les boutons
            for i in range(num_buttons):
                new_value = joystick.get_button(i)
                if new_value != buttons[i]:
                    buttons[i] = new_value
                    something_new = True
            
            # Lire les hats (D-pad)
            for i in range(num_hats):
                new_value = joystick.get_hat(i)
                if new_value != hats[i]:
                    hats[i] = new_value
                    something_new = True
            
            # Lire les balls (trackballs)
            for i in range(num_balls):
                new_value = joystick.get_ball(i)
                if new_value != (0, 0):
                    balls[i] = new_value
                    something_new = True
            
            if something_new:
                stdscr.clear()
                row = 0
                
                stdscr.addstr(row, 0, f"Joystick Name:   '{joystick.get_name()}'")
                row += 1
                stdscr.addstr(row, 0, f"Joystick Number: {joy_id}")
                row += 2
                
                # Afficher les axes
                stdscr.addstr(row, 0, f"Axes {num_axes:2d}:")
                row += 1
                for i in range(num_axes):
                    # Convertir la valeur de l'axe (-1.0 à 1.0) en position pour la barre
                    bar_len = min(40, curses.COLS - 20)
                    pos = int((axes[i] + 1.0) * (bar_len - 1) / 2.0)
                    axis_int = int(axes[i] * 32767)  # Simuler les valeurs SDL
                    bar = print_bar(pos, bar_len)
                    stdscr.addstr(row, 0, f"  {i:2d}: {axis_int:6d}  {bar}")
                    row += 1
                row += 1
                
                # Afficher les boutons
                stdscr.addstr(row, 0, f"Buttons {num_buttons:2d}:")
                row += 1
                for i in range(num_buttons):
                    state = 1 if buttons[i] else 0
                    symbol = "[#]" if buttons[i] else "[ ]"
                    stdscr.addstr(row, 0, f"  {i:2d}: {state}  {symbol}")
                    row += 1
                row += 1
                
                # Afficher les hats
                stdscr.addstr(row, 0, f"Hats {num_hats:2d}:")
                row += 1
                for i in range(num_hats):
                    x, y = hats[i]
                    # Convertir en format SDL hat
                    hat_value = 0
                    if y == 1: hat_value |= 1  # UP
                    if y == -1: hat_value |= 4  # DOWN
                    if x == -1: hat_value |= 8  # LEFT
                    if x == 1: hat_value |= 2   # RIGHT
                    
                    stdscr.addstr(row, 0, f"  {i:2d}: value: {hat_value}")
                    row += 1
                    
                    # Afficher le diagramme du hat
                    up = '1' if y == 1 else '0'
                    down = '1' if y == -1 else '0'
                    left = '1' if x == -1 else '0'
                    right = '1' if x == 1 else '0'
                    
                    # Positions dans le diagramme 3x3
                    ul = 'O' if (y == 1 and x == -1) else ' '
                    u = 'O' if (y == 1 and x == 0) else ' '
                    ur = 'O' if (y == 1 and x == 1) else ' '
                    l = 'O' if (y == 0 and x == -1) else ' '
                    c = 'O' if (y == 0 and x == 0) else ' '
                    r = 'O' if (y == 0 and x == 1) else ' '
                    dl = 'O' if (y == -1 and x == -1) else ' '
                    d = 'O' if (y == -1 and x == 0) else ' '
                    dr = 'O' if (y == -1 and x == 1) else ' '
                    
                    stdscr.addstr(row, 0, f"  +-----+  up:    {up}")
                    row += 1
                    stdscr.addstr(row, 0, f"  |{ul} {u} {ur}|  down:  {down}")
                    row += 1
                    stdscr.addstr(row, 0, f"  |{l} {c} {r}|  left:  {left}")
                    row += 1
                    stdscr.addstr(row, 0, f"  |{dl} {d} {dr}|  right: {right}")
                    row += 1
                    stdscr.addstr(row, 0, "  +-----+")
                    row += 1
                row += 1
                
                # Afficher les balls
                if num_balls > 0:
                    stdscr.addstr(row, 0, f"Balls {num_balls:2d}:")
                    row += 1
                    for i in range(num_balls):
                        x, y = balls[i]
                        stdscr.addstr(row, 0, f"  {i:2d}: {x:6d} {y:6d}")
                        row += 1
                else:
                    stdscr.addstr(row, 0, f"Balls {num_balls:2d}:")
                    row += 1
                row += 1
                
                stdscr.addstr(row, 0, "Press Ctrl-c to exit")
                stdscr.refresh()
            
            # Vérifier les touches
            key = stdscr.getch()
            if key == 3:  # Ctrl-C
                quit_flag = True
            
            clock.tick(30)  # 30 FPS
            
    finally:
        curses.endwin()
        joystick.quit()
        pygame.quit()

def event_joystick(joy_id: int):
    """Affiche les événements de la manette en temps réel"""
    pygame.init()
    pygame.joystick.init()
    
    if joy_id >= pygame.joystick.get_count():
        print(f"Error: Joystick {joy_id} not found")
        return
    
    try:
        joystick = pygame.joystick.Joystick(joy_id)
        joystick.init()
    except pygame.error as e:
        print(f"Unable to open joystick {joy_id}: {e}")
        return
    
    print_joystick_info(joy_id, joystick)
    print("Entering joystick test loop, press Ctrl-c to exit")
    
    clock = pygame.time.Clock()
    
    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION:
                    if event.joy == joy_id:
                        value = int(event.value * 32767)
                        print(f"SDL_JOYAXISMOTION: joystick: {event.joy} axis: {event.axis} value: {value}")
                
                elif event.type == pygame.JOYBUTTONDOWN:
                    if event.joy == joy_id:
                        print(f"SDL_JOYBUTTONDOWN: joystick: {event.joy} button: {event.button} state: 1")
                
                elif event.type == pygame.JOYBUTTONUP:
                    if event.joy == joy_id:
                        print(f"SDL_JOYBUTTONUP: joystick: {event.joy} button: {event.button} state: 0")
                
                elif event.type == pygame.JOYHATMOTION:
                    if event.joy == joy_id:
                        # Convertir en format SDL
                        x, y = event.value
                        hat_value = 0
                        if y == 1: hat_value |= 1   # UP
                        if x == 1: hat_value |= 2   # RIGHT
                        if y == -1: hat_value |= 4  # DOWN
                        if x == -1: hat_value |= 8  # LEFT
                        print(f"SDL_JOYHATMOTION: joystick: {event.joy} hat: {event.hat} value: {hat_value}")
                
                elif event.type == pygame.JOYBALLMOTION:
                    if event.joy == joy_id:
                        print(f"SDL_JOYBALLMOTION: joystick: {event.joy} ball: {event.ball} x: {event.rel[0]} y: {event.rel[1]}")
                
                elif event.type == pygame.JOYDEVICEADDED:
                    print(f"SDL_JOYDEVICEADDED which: {event.device_index}")
                
                elif event.type == pygame.JOYDEVICEREMOVED:
                    print(f"SDL_JOYDEVICEREMOVED which: {event.instance_id}")
                
                elif event.type == pygame.QUIT:
                    return
            
            clock.tick(30)
            
    except KeyboardInterrupt:
        print("Received interrupt, exiting")
    finally:
        joystick.quit()
        pygame.quit()

def test_rumble(joy_id: int):
    """Test les effets de vibration"""
    pygame.init()
    pygame.joystick.init()
    
    if joy_id >= pygame.joystick.get_count():
        print(f"Error: Joystick {joy_id} not found")
        return
    
    try:
        joystick = pygame.joystick.Joystick(joy_id)
        joystick.init()
    except pygame.error as e:
        print(f"Unable to open joystick {joy_id}: {e}")
        return
    
    print(f"Testing rumble on joystick {joy_id}: '{joystick.get_name()}'")
    
    # Méthode 1: Essayer avec pygame (SDL 2.0.18+)
    rumble_success = False
    if hasattr(joystick, 'rumble'):
        try:
            print("Attempting pygame rumble...")
            joystick.rumble(1.0, 1.0, 3000)  # Force faible et forte à 100%, 3 secondes
            rumble_success = True
            print("Pygame rumble started successfully!")
            time.sleep(3)
            joystick.stop_rumble()
            print("Pygame rumble stopped")
        except (pygame.error, AttributeError) as e:
            print(f"Pygame rumble failed: {e}")
    
    # Méthode 2: Utiliser evdev si disponible
    if not rumble_success:
        try:
            import evdev
            rumble_success = test_rumble_evdev(joystick, joy_id)
        except ImportError:
            print("evdev not available, trying direct device access...")
    
    # Méthode 3: Accès direct au device Linux
    if not rumble_success:
        rumble_success = test_rumble_direct(joystick, joy_id)
    
    if not rumble_success:
        print("Rumble not supported or failed on this joystick")
        print("Try installing evdev: pip install evdev")
        print("Or ensure your joystick supports force feedback")
    
    joystick.quit()
    pygame.quit()

def test_rumble_evdev(joystick, joy_id: int) -> bool:
    """Test de vibration avec evdev"""
    try:
        import evdev
        from evdev import InputDevice, ff, ecodes
        
        # Chercher le device correspondant
        device_path = find_evdev_device(joystick)
        if not device_path:
            print("Could not find evdev device for this joystick")
            return False
        
        print(f"Using evdev device: {device_path}")
        device = InputDevice(device_path)
        
        # Vérifier le support des effets de force
        if ecodes.EV_FF not in device.capabilities():
            print("Device does not support force feedback")
            return False
        
        print("Device supports force feedback")
        ff_capabilities = device.capabilities()[ecodes.EV_FF]
        print(f"Force feedback capabilities: {[ecodes.FF[cap] for cap in ff_capabilities if cap in ecodes.FF]}")
        
        # Créer un effet de rumble simple
        if ecodes.FF_RUMBLE in ff_capabilities:
            print("Creating rumble effect...")
            
            # Paramètres de l'effet
            rumble = ff.Rumble(strong_magnitude=0xFFFF, weak_magnitude=0xFFFF)
            duration_ms = 3000
            effect = ff.Effect(
                ecodes.FF_RUMBLE,
                -1,  # id (sera assigné par le kernel)
                0,   # direction
                ff.Trigger(0, 0),
                ff.Replay(duration_ms, 0),
                rumble
            )
            
            # Uploader et jouer l'effet
            effect_id = device.upload_effect(effect)
            print(f"Effect uploaded with ID: {effect_id}")
            
            print("Starting rumble for 3 seconds...")
            device.write(ecodes.EV_FF, effect_id, 1)  # Démarrer l'effet
            time.sleep(3)
            device.write(ecodes.EV_FF, effect_id, 0)  # Arrêter l'effet
            print("Rumble stopped")
            
            # Nettoyer
            device.erase_effect(effect_id)
            device.close()
            return True
        
        elif ecodes.FF_PERIODIC in ff_capabilities:
            print("Trying periodic effect as alternative...")
            
            # Essayer un effet périodique
            periodic = ff.Periodic(
                waveform=ecodes.FF_SINE,
                period=100,  # ms
                magnitude=0x7FFF,
                offset=0,
                phase=0
            )
            
            effect = ff.Effect(
                ecodes.FF_PERIODIC,
                -1,
                0,
                ff.Trigger(0, 0),
                ff.Replay(3000, 0),
                periodic
            )
            
            effect_id = device.upload_effect(effect)
            print(f"Periodic effect uploaded with ID: {effect_id}")
            
            print("Starting periodic effect for 3 seconds...")
            device.write(ecodes.EV_FF, effect_id, 1)
            time.sleep(3)
            device.write(ecodes.EV_FF, effect_id, 0)
            print("Effect stopped")
            
            device.erase_effect(effect_id)
            device.close()
            return True
        
        else:
            print("No compatible force feedback effects found")
            device.close()
            return False
    
    except Exception as e:
        print(f"evdev rumble failed: {e}")
        return False

def find_evdev_device(joystick) -> Optional[str]:
    """Trouve le chemin evdev correspondant à la manette pygame"""
    try:
        import evdev
        
        joystick_name = joystick.get_name()
        
        # Chercher dans /dev/input/
        for device_path in glob.glob('/dev/input/event*'):
            try:
                device = evdev.InputDevice(device_path)
                if device.name == joystick_name:
                    device.close()
                    return device_path
                device.close()
            except (OSError, PermissionError):
                continue
        
        return None
    except ImportError:
        return None

def test_rumble_direct(joystick, joy_id: int) -> bool:
    """Test de vibration avec accès direct au device (méthode basique)"""
    try:
        # Cette méthode est très basique et peut ne pas fonctionner sur tous les systèmes
        joystick_name = joystick.get_name().lower()
        
        # Chercher le device js correspondant
        js_devices = glob.glob('/dev/input/js*')
        
        for js_path in js_devices:
            try:
                # Essayer d'ouvrir le device en écriture
                with open(js_path, 'wb') as f:
                    # Commande de rumble très basique (peut ne pas fonctionner)
                    # Ceci est un hack et n'est pas garanti de fonctionner
                    print(f"Attempting basic rumble on {js_path}...")
                    
                    # Cette approche est très limitée et spécifique à certaines manettes
                    if 'xbox' in joystick_name or 'controller' in joystick_name:
                        # Commande rumble Xbox (exemple, peut ne pas fonctionner)
                        rumble_data = b'\x00\x08\x00\x00\xFF\xFF\x00\x00'
                        f.write(rumble_data)
                        f.flush()
                        print("Basic rumble command sent")
                        time.sleep(1)
                        
                        # Arrêter le rumble
                        stop_data = b'\x00\x08\x00\x00\x00\x00\x00\x00'
                        f.write(stop_data)
                        f.flush()
                        print("Basic rumble stopped")
                        return True
                        
            except (OSError, PermissionError) as e:
                continue
        
        print("Direct device access method not supported")
        return False
        
    except Exception as e:
        print(f"Direct rumble method failed: {e}")
        return False

def test_forcefeedback(joy_id: int):
    """Test complet des effets de force feedback (pour volants principalement)"""
    pygame.init()
    pygame.joystick.init()
    
    if joy_id >= pygame.joystick.get_count():
        print(f"Error: Joystick {joy_id} not found")
        return
    
    try:
        joystick = pygame.joystick.Joystick(joy_id)
        joystick.init()
    except pygame.error as e:
        print(f"Unable to open joystick {joy_id}: {e}")
        return
    
    print(f"Testing force feedback on device {joy_id}: '{joystick.get_name()}'")
    
    try:
        import evdev
        test_advanced_forcefeedback(joystick, joy_id)
    except ImportError:
        print("evdev not available. Force feedback requires evdev.")
        print("Install with: pip install evdev")
    
    joystick.quit()
    pygame.quit()

def test_advanced_forcefeedback(joystick, joy_id: int):
    """Test avancé des effets de force feedback avec evdev"""
    try:
        import evdev
        from evdev import InputDevice, ff, ecodes
        
        device_path = find_evdev_device(joystick)
        if not device_path:
            print("Could not find evdev device for this joystick")
            return
        
        print(f"Using evdev device: {device_path}")
        device = InputDevice(device_path)
        
        if ecodes.EV_FF not in device.capabilities():
            print("Device does not support force feedback")
            device.close()
            return
        
        ff_capabilities = device.capabilities()[ecodes.EV_FF]
        print("Force feedback capabilities detected:")
        
        # Analyser les capacités
        capabilities = []
        for cap in ff_capabilities:
            if cap in ecodes.FF:
                cap_name = ecodes.FF[cap]
                capabilities.append((cap, cap_name))
                print(f"  - {cap_name} (0x{cap:02X})")
        
        if not capabilities:
            print("No force feedback effects available")
            device.close()
            return
        
        print("\nStarting force feedback test sequence...")
        print("Each effect will last 3 seconds\n")
        
        effects_tested = 0
        
        # Test 1: Effet constant (résistance constante)
        if ecodes.FF_CONSTANT in ff_capabilities:
            print("1. Testing CONSTANT force (steering resistance)...")
            try:
                constant = ff.Constant(level=0x4000, envelope=ff.Envelope(0, 0, 0, 0))
                effect = ff.Effect(
                    ecodes.FF_CONSTANT,
                    -1, 0,  # id, direction
                    ff.Trigger(0, 0),
                    ff.Replay(3000, 0),
                    constant
                )
                
                effect_id = device.upload_effect(effect)
                device.write(ecodes.EV_FF, effect_id, 1)
                time.sleep(3)
                device.write(ecodes.EV_FF, effect_id, 0)
                device.erase_effect(effect_id)
                print("   ✓ Constant force test completed")
                effects_tested += 1
            except Exception as e:
                print(f"   ✗ Constant force failed: {e}")
        
        # Test 2: Effet de ressort (spring effect)
        if ecodes.FF_SPRING in ff_capabilities:
            print("2. Testing SPRING effect (centering force)...")
            try:
                spring = ff.Condition(
                    right_saturation=0x7FFF, left_saturation=0x7FFF,
                    right_coeff=0x4000, left_coeff=0x4000,
                    deadband=0x100, center=0
                )
                effect = ff.Effect(
                    ecodes.FF_SPRING,
                    -1, 0,
                    ff.Trigger(0, 0),
                    ff.Replay(3000, 0),
                    spring
                )
                
                effect_id = device.upload_effect(effect)
                device.write(ecodes.EV_FF, effect_id, 1)
                time.sleep(3)
                device.write(ecodes.EV_FF, effect_id, 0)
                device.erase_effect(effect_id)
                print("   ✓ Spring effect test completed")
                effects_tested += 1
            except Exception as e:
                print(f"   ✗ Spring effect failed: {e}")
        
        # Test 3: Effet d'amortissement (damper)
        if ecodes.FF_DAMPER in ff_capabilities:
            print("3. Testing DAMPER effect (velocity damping)...")
            try:
                damper = ff.Condition(
                    right_saturation=0x7FFF, left_saturation=0x7FFF,
                    right_coeff=0x2000, left_coeff=0x2000,
                    deadband=0x100, center=0
                )
                effect = ff.Effect(
                    ecodes.FF_DAMPER,
                    -1, 0,
                    ff.Trigger(0, 0),
                    ff.Replay(3000, 0),
                    damper
                )
                
                effect_id = device.upload_effect(effect)
                device.write(ecodes.EV_FF, effect_id, 1)
                time.sleep(3)
                device.write(ecodes.EV_FF, effect_id, 0)
                device.erase_effect(effect_id)
                print("   ✓ Damper effect test completed")
                effects_tested += 1
            except Exception as e:
                print(f"   ✗ Damper effect failed: {e}")
        
        # Test 4: Effet d'inertie
        if ecodes.FF_INERTIA in ff_capabilities:
            print("4. Testing INERTIA effect (mass simulation)...")
            try:
                inertia = ff.Condition(
                    right_saturation=0x7FFF, left_saturation=0x7FFF,
                    right_coeff=0x3000, left_coeff=0x3000,
                    deadband=0x100, center=0
                )
                effect = ff.Effect(
                    ecodes.FF_INERTIA,
                    -1, 0,
                    ff.Trigger(0, 0),
                    ff.Replay(3000, 0),
                    inertia
                )
                
                effect_id = device.upload_effect(effect)
                device.write(ecodes.EV_FF, effect_id, 1)
                time.sleep(3)
                device.write(ecodes.EV_FF, effect_id, 0)
                device.erase_effect(effect_id)
                print("   ✓ Inertia effect test completed")
                effects_tested += 1
            except Exception as e:
                print(f"   ✗ Inertia effect failed: {e}")
        
        # Test 5: Effet de friction
        if ecodes.FF_FRICTION in ff_capabilities:
            print("5. Testing FRICTION effect...")
            try:
                friction = ff.Condition(
                    right_saturation=0x7FFF, left_saturation=0x7FFF,
                    right_coeff=0x4000, left_coeff=0x4000,
                    deadband=0x100, center=0
                )
                effect = ff.Effect(
                    ecodes.FF_FRICTION,
                    -1, 0,
                    ff.Trigger(0, 0),
                    ff.Replay(3000, 0),
                    friction
                )
                
                effect_id = device.upload_effect(effect)
                device.write(ecodes.EV_FF, effect_id, 1)
                time.sleep(3)
                device.write(ecodes.EV_FF, effect_id, 0)
                device.erase_effect(effect_id)
                print("   ✓ Friction effect test completed")
                effects_tested += 1
            except Exception as e:
                print(f"   ✗ Friction effect failed: {e}")
        
        # Test 6: Effet périodique (vibrations, oscillations)
        if ecodes.FF_PERIODIC in ff_capabilities:
            print("6. Testing PERIODIC effects...")
            
            # Test sine wave
            print("   6a. Sine wave...")
            try:
                sine = ff.Periodic(
                    waveform=ecodes.FF_SINE,
                    period=200,  # 200ms period
                    magnitude=0x4000,
                    offset=0,
                    phase=0,
                    envelope=ff.Envelope(500, 0, 0, 500)  # fade in/out
                )
                effect = ff.Effect(
                    ecodes.FF_PERIODIC,
                    -1, 0,
                    ff.Trigger(0, 0),
                    ff.Replay(3000, 0),
                    sine
                )
                
                effect_id = device.upload_effect(effect)
                device.write(ecodes.EV_FF, effect_id, 1)
                time.sleep(3)
                device.write(ecodes.EV_FF, effect_id, 0)
                device.erase_effect(effect_id)
                print("      ✓ Sine wave test completed")
            except Exception as e:
                print(f"      ✗ Sine wave failed: {e}")
            
            # Test square wave
            print("   6b. Square wave...")
            try:
                square = ff.Periodic(
                    waveform=ecodes.FF_SQUARE,
                    period=150,
                    magnitude=0x3000,
                    offset=0,
                    phase=0,
                    envelope=ff.Envelope(300, 0, 0, 300)
                )
                effect = ff.Effect(
                    ecodes.FF_PERIODIC,
                    -1, 0,
                    ff.Trigger(0, 0),
                    ff.Replay(3000, 0),
                    square
                )
                
                effect_id = device.upload_effect(effect)
                device.write(ecodes.EV_FF, effect_id, 1)
                time.sleep(3)
                device.write(ecodes.EV_FF, effect_id, 0)
                device.erase_effect(effect_id)
                print("      ✓ Square wave test completed")
            except Exception as e:
                print(f"      ✗ Square wave failed: {e}")
            
            effects_tested += 1
        
        # Test 7: Effet de rampe (force qui change graduellement)
        if ecodes.FF_RAMP in ff_capabilities:
            print("7. Testing RAMP effect (gradual force change)...")
            try:
                ramp = ff.Ramp(
                    start_level=-0x4000,  # Commence vers la gauche
                    end_level=0x4000,     # Finit vers la droite
                    envelope=ff.Envelope(500, 0, 0, 500)
                )
                effect = ff.Effect(
                    ecodes.FF_RAMP,
                    -1, 0,
                    ff.Trigger(0, 0),
                    ff.Replay(3000, 0),
                    ramp
                )
                
                effect_id = device.upload_effect(effect)
                device.write(ecodes.EV_FF, effect_id, 1)
                time.sleep(3)
                device.write(ecodes.EV_FF, effect_id, 0)
                device.erase_effect(effect_id)
                print("   ✓ Ramp effect test completed")
                effects_tested += 1
            except Exception as e:
                print(f"   ✗ Ramp effect failed: {e}")
        
        # Test 8: Test de rumble (si disponible)
        if ecodes.FF_RUMBLE in ff_capabilities:
            print("8. Testing RUMBLE effect...")
            try:
                rumble = ff.Rumble(strong_magnitude=0x8000, weak_magnitude=0x4000)
                effect = ff.Effect(
                    ecodes.FF_RUMBLE,
                    -1, 0,
                    ff.Trigger(0, 0),
                    ff.Replay(3000, 0),
                    rumble
                )
                
                effect_id = device.upload_effect(effect)
                device.write(ecodes.EV_FF, effect_id, 1)
                time.sleep(3)
                device.write(ecodes.EV_FF, effect_id, 0)
                device.erase_effect(effect_id)
                print("   ✓ Rumble effect test completed")
                effects_tested += 1
            except Exception as e:
                print(f"   ✗ Rumble effect failed: {e}")
        
        print(f"\nForce feedback test completed!")
        print(f"Successfully tested {effects_tested} effect types")
        
        if effects_tested == 0:
            print("No effects could be tested. This may indicate:")
            print("- Device doesn't support force feedback")
            print("- Permission issues (try running as root or add user to input group)")
            print("- Driver issues")
        
        device.close()
        
    except Exception as e:
        print(f"Force feedback test failed: {e}")
        print("Make sure you have:")
        print("- evdev installed (pip install evdev)")
        print("- Proper permissions to access /dev/input/event* devices")
        print("- A device that supports force feedback")

def print_help(program_name: str):
    """Affiche l'aide du programme"""
    print(f"Usage: {program_name} [OPTION]")
    print("List available joysticks or test a joystick.")
    print("This program uses pygame (SDL) for testing instead of using the raw")
    print("/dev/input/jsX interface")
    print()
    print("Options:")
    print("  -h, --help             Print this help")
    print("  --version              Print version number and exit")
    print("  -l, --list             Search for available joysticks and list their properties")
    print("  -t, --test JOYNUM      Display a graphical representation of the current joystick state")
    print("  -e, --event JOYNUM     Display the events that are received from the joystick")
    print("  -r, --rumble JOYNUM    Test rumble effects on gamepad JOYNUM (requires evdev)")
    print("  -f, --forcefeedback JOYNUM")
    print("                         Test advanced force feedback effects on wheel JOYNUM")
    print()
    print("Dependencies for rumble/force feedback support:")
    print("  pip install evdev")
    print("  Make sure you have permission to access /dev/input/event* devices")
    print()
    print("Examples:")
    print(f"  {program_name} --list")
    print(f"  {program_name} --test 0")

def main():
    parser = argparse.ArgumentParser(description='Joystick Test Program for SDL (Python version)')
    parser.add_argument('--version', action='store_true', help='Print version number and exit')
    parser.add_argument('-l', '--list', action='store_true', help='List available joysticks')
    parser.add_argument('-t', '--test', type=int, metavar='JOYNUM', help='Test joystick JOYNUM')
    parser.add_argument('-e', '--event', type=int, metavar='JOYNUM', help='Show events from joystick JOYNUM')
    parser.add_argument('-r', '--rumble', type=int, metavar='JOYNUM', help='Test rumble on joystick JOYNUM')
    parser.add_argument('-f', '--forcefeedback', type=int, metavar='JOYNUM', help='Test force feedback effects on joystick JOYNUM')
    
    if len(sys.argv) == 1:
        print_help(sys.argv[0])
        sys.exit(1)
    
    args = parser.parse_args()
    
    if args.version:
        print(f"sdl2-jstest {VERSION}")
        sys.exit(0)
    elif args.list:
        list_joysticks()
    elif args.test is not None:
        test_joystick(args.test)
    elif args.event is not None:
        event_joystick(args.event)
    elif args.rumble is not None:
        test_rumble(args.rumble)
    elif args.forcefeedback is not None:
        test_forcefeedback(args.forcefeedback)
    else:
        print_help(sys.argv[0])

if __name__ == "__main__":
    main()
