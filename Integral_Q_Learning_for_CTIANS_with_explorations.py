import numpy as np
import matplotlib.pyplot as plt

'''This code is an implementation of the first example of this article:
    Integral Reinforcement Learning for Continuous-Time Input-Affine Nonlinear Systems 
    With Simultaneous Invariant Explorations
    using Algorithm 3: Integral Q-learning I 
'''

dt = 0.01
S = np.eye(2)
R = 1
theta = np.array([[1]])  # Weight Vector
iteration_time = 30  # The number of data collected per iteration
sample_time = 25
T = 0.1  # The time step between every sample of the system


def h(x):  # Affine function of the input
    return np.sin(x)


def phi(x):  # The nonlinear regression function
    return np.array([[np.sin(x)]])


def sim(X, V, S, R, e, time):  # Simulate the system
    x_1 = [X[0][0]]
    x_2 = [X[1][0]]
    cost_original = 0
    cost_exploration = 0
    XT = np.zeros((X.shape[0], 1))
    for i in range(X.shape[0]):
        XT[i][0] = X[i][0]
    for t in range(int(T / dt)):
        rho = np.kron(XT, phi(X[0][0]))
        U = np.matmul(V.T, rho)
        X_dot = np.zeros((2, 1))
        X_dot[0] = -XT[0][0] + XT[1][0]  # The differential equations of the system
        X_dot[1] = -(XT[0][0] + XT[1][0]) / 2 + XT[1][0] * (h(XT[0][0]) ** 2) / 2 + h(XT[0][0]) * (U + e)
        XT += X_dot * dt
        cost = np.matmul(np.matmul(XT.T, S), XT) + U * R * U
        cost_original += cost * dt  # cost function
        XB = np.zeros((3, 1))
        XB[1][0] = -(XT[0][0] * phi(XT[0][0])[0][0] / 2)
        XB[2][0] = -(XT[1][0] * phi(XT[0][0])[0][0])
        cost_exploration += 2 * XB * R * e * dt
        time += dt
        x_1.append(XT[0][0])
        x_2.append(XT[1][0])
    return cost_original, cost_exploration, XT, time, x_1, x_2


def main():
    X = np.array([[0.5],
                  [-0.5]])  # Initial state
    iteration_table = [0]
    time_table = []
    X_1_table = []
    X_2_table = []
    wi_1_table = [-1]
    wi_2_table = [3]
    wi_3_table = [1.5]
    vi_1_table = [-3/2]
    vi_2_table = [-3/2]
    time = 0
    v = np.array([[-3/2],
                  [-3/2]])
    V = np.kron(v, theta)  # The weight vector of actor NN
    W = np.array([[-1],
                  [3],
                  [1.5]])  # The weight vector of critic NN
    for i in range(int(sample_time / (iteration_time * T))):  # iterating
        x_estimate = np.zeros((int(X.shape[0] * (X.shape[0] + 1) / 2), iteration_time))
        xt_estimate = np.zeros((int(X.shape[0] * (X.shape[0] + 1) / 2), iteration_time))
        Y_estimate = np.zeros((iteration_time, 1))
        E_estimate = np.zeros((int(X.shape[0] * (X.shape[0] + 1) / 2), iteration_time))
        for N in range(iteration_time):  # Sampling
            if N < int(iteration_time / 2):
                e = 2.5
            else:
                e = -2.5  # exploration
            x_estimate[0][N] = X[0][0] ** 2
            x_estimate[1][N] = X[0][0] * X[1][0]
            x_estimate[2][N] = X[1][0] ** 2
            cost_original, cost_exploration, X, time, x_1, x_2 = sim(X, V, S, R, e, time)  # Simulating
            ct_table = np.linspace(T * N + i * iteration_time * T, T * (N + 1) + i * iteration_time * T, len(x_1)).tolist()
            plt.figure('Trajectories of x1')
            plt.title('Trajectories of x1')
            plt.ylim(-0.5, 0.5)
            plt.plot(ct_table, x_1, color='blue', label="x1")
            plt.grid()
            plt.figure('Trajectories of x2')
            plt.title('Trajectories of x2')
            plt.ylim(-1.0, 0.2)
            plt.plot(ct_table, x_2, color='blue', label="x2")
            plt.grid()
            xt_estimate[0][N] = X[0][0] ** 2
            xt_estimate[1][N] = X[0][0] * X[1][0]
            xt_estimate[2][N] = X[1][0] ** 2
            E_estimate[0][N] = cost_exploration[0][0]
            E_estimate[1][N] = cost_exploration[1][0]
            E_estimate[2][N] = cost_exploration[2][0]
            Y_estimate[N][0] = cost_original
        X_estimate = x_estimate - xt_estimate - E_estimate
        W = np.matmul(X_estimate, X_estimate.T)
        W = np.linalg.inv(W)
        W = np.matmul(W, X_estimate)
        W = np.matmul(W, Y_estimate)  # update the weight vector of critic NN
        v = np.array([[-W[1][0] / 2],
                     [-W[2][0]]])
        V = np.kron(v, theta)  # update the weight vector of actor NN
        iteration_table.append(i + 1)
        time_table.append(iteration_time * T * (i + 1))
        wi_1_table.append(W[0][0])
        wi_2_table.append(W[1][0])
        wi_3_table.append(W[2][0])
        vi_1_table.append(V[0][0])
        vi_2_table.append(V[1][0])
        X_1_table.append(X[0][0])
        X_2_table.append(X[1][0])
        print('wi', i + 1, ':', W)
        print('vi', i + 1, ':', V)
        plt.figure('Trajectories of x1')
        plt.scatter(time_table, X_1_table, color='blue')
        plt.figure('Trajectories of x2')
        plt.scatter(time_table, X_2_table, color='blue')
    for j in range(int((sample_time - (i + 1) * iteration_time * T) / T)):
        cost_original, cost_exploration, X, time, x_1, x_2 = sim(X, V, S, R, e, time)
        ct_table = np.linspace(j * T + iteration_time * T * (i + 1), (j + 1) * T + iteration_time * T * (i + 1), len(x_1)).tolist()
        plt.figure('Trajectories of x1')
        plt.plot(ct_table, x_1, color='blue', label="x1")
        plt.figure('Trajectories of x2')
        plt.plot(ct_table, x_2, color='blue', label="x2")

    plt.figure('Evolution of the critic weights wi')
    plt.title('Evolution of the critic weights wi')
    plt.grid()
    plt.plot(iteration_table, wi_1_table, color='blue', linestyle='--', label="wi1", marker='.')
    plt.plot(iteration_table, wi_2_table, color='cyan', linestyle='--', label="wi2", marker='x')
    plt.plot(iteration_table, wi_3_table, color='green', linestyle='--', label="wi3", marker='s')
    plt.legend(['wi1', 'wi2', 'wi3'])

    plt.figure('Evolution of the actor weights vi')
    plt.title('Evolution of the actor weights vi')
    plt.grid()
    plt.plot(iteration_table, vi_1_table, color='green', linestyle='--', label="vi1", marker='.')
    plt.plot(iteration_table, vi_2_table, color='red', linestyle='--', label="vi2", marker='s')
    plt.legend(['vi1', 'vi2'])
    plt.pause(1000)


main()
