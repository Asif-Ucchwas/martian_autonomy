"""Suited astronaut walking capability on Mars.
MartianAutonomy | NASA Space Apps 2026 | Made with AI assistance (Claude)

Sources:
  [M02] Minetti et al. 2002, J Appl Physiol 93:1039 - measured net metabolic
        cost of walking Cw (J/kg/m) on gradients -0.45..+0.45 (Table 2).
  [K97] Kram, Domingo & Ferris 1997, J Exp Biol 200:821 - walk-run transition
        at the same Froude number (~0.5) in reduced gravity -> walking speed
        scales with sqrt(g).
  [N10] Norcross et al. 2010, NASA/TP-2010-216125 - MKIII suit tested at
        121 kg incl. PLSS mock-up; suited inclined walking at 0.56-0.97 m/s,
        grades 0-30 %; the shirtsleeve baseline accounts for most of the
        incline cost and suit pressure contributed little.
  [S16] Norcross et al. (Aerosp Med Hum Perform 87:4) - suit WEIGHT drives the
        biggest metabolic differences between suits; pressure makes little.

Model (assumptions stated):
  1. Metabolic cost scales with the total weight carried (body + suit) [N10, S16].
     On Mars: (80 + 121 kg) x 3.71 = 746 N, vs an 80 kg person on Earth: 785 N.
  2. Shape of cost vs slope = human data [M02], scaled by that weight ratio.
  3. Flat-ground speed = Earth preferred speed x sqrt(g_mars/g_earth) [K97];
     cross-checked against NASA's suited test speeds 0.56-0.97 m/s [N10].
  4. Constant effort: the astronaut slows uphill so metabolic power stays at
     the flat-walking value (conservative).
  5. Remaining suit penalties (joint stiffness etc.) not quantified -> SUIT_PENALTY
     defaults to 1.0; raise it to make the astronaut slower everywhere.
Limits:
  - SOFT limit 16.7 deg (30 % grade): the steepest grade NASA tested in a suit.
  - HARD limit 24.2 deg (45 % grade): the steepest grade with human data at all.
  - Mars suited weight (746 N) is ABOVE NASA's heaviest suited test (~654 N).
"""
import numpy as np

G_EARTH, G_MARS = 9.81, 3.71
M_BODY = 80.0          # kg, typical astronaut (NASA test subjects averaged 80.7 kg)
M_SUIT = 121.0         # kg, MKIII + PLSS mock-up as tested by NASA [N10]
LEG = 0.90             # m, typical adult leg length (assumed)
SUIT_PENALTY = 1.0     # >1 = extra cost from suit stiffness (unquantified)

# [M02] Table 2: minimum net Cw (J/kg/m) per gradient, unsuited, Earth
I  = np.array([-0.45,-0.40,-0.35,-0.30,-0.20,-0.10, 0.00, 0.10, 0.20, 0.30, 0.35, 0.40, 0.45])
CW = np.array([ 3.46, 3.23, 2.65, 2.18, 1.30, 0.81, 1.64, 4.68, 8.07,11.29,12.72,14.75,17.33])
V_PREF_EARTH = 1.0     # m/s, speed of minimum level cost [M02]

W_SUITED_MARS = (M_BODY + M_SUIT) * G_MARS
W_BODY_EARTH  = M_BODY * G_EARTH
WEIGHT_RATIO  = W_SUITED_MARS / W_BODY_EARTH

V_FLAT = V_PREF_EARTH * np.sqrt(G_MARS / G_EARTH)      # [K97]
V_MAX_WALK = np.sqrt(0.5 * G_MARS * LEG)               # Froude 0.5
SOFT_DEG = np.degrees(np.arctan(0.30))                 # [N10]
HARD_DEG = np.degrees(np.arctan(0.45))                 # [M02]

def cost(i, weight_ratio=WEIGHT_RATIO, penalty=SUIT_PENALTY):
    """Net metabolic cost, J per kg of BODY mass per metre, at gradient i."""
    return np.interp(i, I, CW) * weight_ratio * penalty

def speed(slope_deg, weight_ratio=WEIGHT_RATIO, penalty=SUIT_PENALTY):
    """Suited walking speed on Mars (m/s) at a signed slope; 0 = impassable."""
    i = np.tan(np.radians(slope_deg))
    if abs(slope_deg) > HARD_DEG:
        return 0.0
    power = cost(0.0, weight_ratio, penalty) * V_FLAT            # W per kg body
    return float(min(power / cost(i, weight_ratio, penalty), V_MAX_WALK))

if __name__ == "__main__":
    unsuited_ratio = (M_BODY * G_MARS) / W_BODY_EARTH
    print(f"Suited weight on Mars : {W_SUITED_MARS:.0f} N  vs  body on Earth {W_BODY_EARTH:.0f} N  "
          f"(ratio {WEIGHT_RATIO:.2f})")
    print(f"Unsuited on Mars      : ratio {unsuited_ratio:.2f}")
    print(f"Flat-ground speed     : {V_FLAT:.2f} m/s ({V_FLAT*3.6:.1f} km/h); NASA suited tests used 0.56-0.97")
    print(f"Power on flat ground  : {cost(0)*V_FLAT*M_BODY:.0f} W net (suited)  vs  "
          f"{cost(0, unsuited_ratio)*V_FLAT*M_BODY:.0f} W unsuited")
    print(f"Limits                : soft {SOFT_DEG:.1f} deg (NASA suited data edge), "
          f"hard {HARD_DEG:.1f} deg (human data edge)\n")
    print(" slope | suited up  down | effort x to hold flat speed uphill")
    for d in [0, 5, 10, 15, 16.7, 20, 24]:
        up, dn = speed(d), speed(-d)
        x = cost(np.tan(np.radians(d))) / cost(0)
        flag = "  <- beyond suited data" if d > SOFT_DEG + 0.05 else ""
        print(f" {d:>5} |   {up:.2f}   {dn:.2f}  |   {x:4.1f}x{flag}")
    print(f"\n10 km walk-back, flat: {10000/V_FLAT/3600:.1f} h")
    for d in [5, 10, 15]:
        print(f"10 km walk-back, all {d:>2} deg uphill: {10000/speed(d)/3600:.1f} h")
