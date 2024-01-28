from src.mma import Mma
import numpy as np


def main():
    # Definição das variáveis de projeto
    r_r = 40e-3
    mma = Mma(np.matrix('1, 0, 1; 0, -1, -1; 0, 1, 1; 1, 0, -1; -1, 0, 1; 0, 1, -1; 0, -1, 1;-1 0 -1'),
              1e-3, 0.6, r_r, 0.473, 0, 500, 75,
              75, 1)

    # Dimensionamento do MMA
    mma.design(log_results=True)

    # Desenho do MMA
    mma.draw(save_result=True, hold_draw=True)


if __name__ == '__main__':
    main()
