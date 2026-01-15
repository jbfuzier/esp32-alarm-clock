import asyncio
import machine

# Define buttons
buttons = {
    'button1': machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP),
    'button2': machine.Pin(1, machine.Pin.IN, machine.Pin.PULL_UP),
}

async def handle_button(button_name):
    while True:
        if not buttons[button_name].value():  # If button is pressed
            print(f'{button_name} pressed')
            await asyncio.sleep(0.2)  # debounce delay
        await asyncio.sleep(0.01)  # Short delay to avoid busy-waiting

async def main():
    await asyncio.gather(
        handle_button('button1'),
        handle_button('button2'),
    )

if __name__ == '__main__':
    asyncio.run(main())