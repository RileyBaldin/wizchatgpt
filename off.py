import asyncio
from pywizlight import wizlight, discovery

async def turn_off_all_wiz_bulbs():
    print("Discovering Philips Wiz bulbs on the network...")
    
    bulbs = await discovery.discover_lights(broadcast_space="255.255.255.255")  # Adjust for your subnet if needed

    if not bulbs:
        print("No Wiz bulbs found on the network.")
        return

    print(f"Found {len(bulbs)} bulbs:")
    bulb_objects = [wizlight(bulb.ip) for bulb in bulbs]

    # Turn off all detected bulbs
    for bulb in bulb_objects:
        print(f"Turning off bulb at IP: {bulb.ip}")
        await bulb.turn_off()

    print("All Wiz bulbs have been turned off.")

    # Ensure proper cleanup
    for bulb in bulb_objects:
        await bulb.async_close()

# Fix for event loop issue
if __name__ == "__main__":
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # If no event loop is running
        loop = None

    if loop and loop.is_running():
        print("Detected running event loop. Using alternative execution method.")
        task = loop.create_task(turn_off_all_wiz_bulbs())
        loop.run_until_complete(task)
    else:
        asyncio.run(turn_off_all_wiz_bulbs())

    # Explicitly close the loop (if necessary)
    if loop:
        loop.close()