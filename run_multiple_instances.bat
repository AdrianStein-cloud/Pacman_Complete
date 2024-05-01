for /l %%x in (1, 1, 70) do (
  	timeout /t 0.1
	start python qlearning.py
)