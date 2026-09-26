import matplotlib.pyplot as plt
import numpy as np

# Data
U2 = 3.613
Vr2 = 0.192
beta2 = 30 # degrees
Vu2 = 3.281

# Coordinates
# Start origin at (0,0)
# U2 vector: from (0,0) to (U2, 0)
# V2 (absolute velocity) vector: from (0,0) to (Vu2, Vr2)
# W2 (relative velocity) vector: from (U2, 0) to (Vu2, Vr2)

fig, ax = plt.subplots(figsize=(10, 4))

# Plot vectors
# U2
ax.annotate('', xy=(U2, 0), xytext=(0, 0), arrowprops=dict(arrowstyle="->", color='blue', lw=2))
# V2
ax.annotate('', xy=(Vu2, Vr2), xytext=(0, 0), arrowprops=dict(arrowstyle="->", color='red', lw=2))
# W2
ax.annotate('', xy=(Vu2, Vr2), xytext=(U2, 0), arrowprops=dict(arrowstyle="->", color='green', lw=2))

# Plot dashed lines for components
ax.plot([Vu2, Vu2], [0, Vr2], 'k--', alpha=0.5) # Vr2 vertical line
ax.plot([0, Vu2], [Vr2, Vr2], 'k--', alpha=0.2) # Horizontal line at Vr2

# Labels
ax.text(U2/2, -0.02, f'U₂ = {U2:.3f} m/s', ha='center', va='top', color='blue', fontsize=12, fontweight='bold')
ax.text(Vu2/2, Vr2/2 + 0.01, f'V₂', ha='right', va='bottom', color='red', fontsize=12, fontweight='bold')
ax.text((U2+Vu2)/2 + 0.05, Vr2/2, f'W₂', ha='left', va='bottom', color='green', fontsize=12, fontweight='bold')
ax.text(Vu2, Vr2/2, f'Vr₂ = {Vr2:.3f} m/s', ha='right', va='center', color='black', fontsize=10)
ax.text(Vu2/2, 0.01, f'Vu₂ = {Vu2:.3f} m/s', ha='center', va='bottom', color='black', fontsize=10)

# Angle beta2
# Arc for beta2
theta = np.linspace(150, 180, 100)
r = 0.4
x_arc = U2 + r * np.cos(np.radians(theta))
y_arc = 0 + r * np.sin(np.radians(theta))
ax.plot(x_arc, y_arc, 'k-')
ax.text(U2 - 0.5, 0.03, f'β₂=30°', color='green', fontsize=12, fontweight='bold')

# Formatting
ax.set_aspect('equal')
# We need to stretch Y artificially to make it visible since Vr2 is so small
ax.set_ylim(-0.1, Vr2 + 0.1)
ax.set_xlim(-0.2, U2 + 0.2)
ax.axis('off')

plt.title('Outlet Velocity Triangle (Impeller Tip)', fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('Velocity_Triangle_Outlet.png', dpi=300, bbox_inches='tight')
print("Velocity triangle saved as Velocity_Triangle_Outlet.png")
