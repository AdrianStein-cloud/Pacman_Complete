for /l %%x in (1, 1, 50) do (
  	timeout /t 1
	start python qlearning.py
)