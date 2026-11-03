# CPU Scheduling Simulator

Project Overview:

The CPU Scheduling Simulator is a Python-based, console application developed as an Operating Systems mini project. It simulates CPU scheduling algorithms and helps users understand how processes are selected for execution.

Features:

- Implements FCFS, SJF, Priority Scheduling, and Round Robin.
- Displays process execution using a Gantt chart.
- Calculates completion time, waiting time, and turnaround time.
- Displays average waiting time and average turnaround time.

Technologies Used:
- Python
- VS Code

How to Run :
python main.py

Objective:
To understand CPU scheduling algorithms and compare their performance through practical implementation.
#include <stdio.h>

int main()
{
    int a[100], n, i, j, temp;

    printf("Enter number of elements: ");
    scanf("%d", &n);

    printf("Enter elements: ");
    for(i = 0; i < n; i++)
    {
        scanf("%d", &a[i]);
    }

    for(i = 0; i < n - 1; i++)
    {
        for(j = 0; j < n - i - 1; j++)
        {
            if(a[j] > a[j + 1])
            {
                temp = a[j];
                a[j] = a[j + 1];
                a[j + 1] = temp;
            }
        }
    }

    printf("Sorted array: ");
    for(i = 0; i < n; i++)
    {
        printf("%d ", a[i]);
    }

    return 0;
}