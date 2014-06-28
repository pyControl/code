import PyControl as pc
import examples  as ex 

b = ex.blinker()      # Create an instance of blinker object.

pc.register_machine(b) # Register it with PyControl.

pc.run_machines(10000)  # Run PyControl for 10000 cycles.







