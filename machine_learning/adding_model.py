import torch
try:
    # Attempt to set device to DirectML if available
    device = torch.device("dml")
    # Create a tensor on the DirectML device
    x = torch.ones(5, 5, device=device)
    y = x + 2
    print("DirectML device is working on Ryzen GPU!")
    print("Tensor:", y)
except Exception as e:
    print("DirectML is not available on this device or encountered an issue.")
    print("Error:", e)
