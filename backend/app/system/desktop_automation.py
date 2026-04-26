import logging
from typing import Any

from app.core.system_controller import SystemController

logger = logging.getLogger(__name__)

try:
    import pyautogui

    # Configure PyAutoGUI safety features
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1
    HAS_PYAUTOGUI = True
except ImportError:
    logger.warning("PyAutoGUI not found. Desktop automation disabled.")
    HAS_PYAUTOGUI = False

# HAS_PYWINAUTO flag for future use or downstream compatibility
HAS_PYWINAUTO = False


class DesktopAutomation(SystemController):
    """Handles desktop automation operations"""

    async def type_text(
        self, text: str, interval: float = 0.0, approval_callback: callable | None = None
    ) -> dict[str, Any]:
        """
        Type text using keyboard simulation

        Args:
            text: Text to type
            interval: Interval between keystrokes (seconds)
            approval_callback: Approval callback

        Returns:
            Dictionary with operation result
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            pyautogui.write(params["text"], interval=params["interval"])
            return {"text": params["text"], "characters": len(params["text"])}

        return await self.execute_operation(
            operation_type="keyboard_type",
            description=f"Type text: {text[:50]}...",
            parameters={"text": text, "interval": interval},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def press_key(
        self,
        key: str,
        presses: int = 1,
        interval: float = 0.0,
        approval_callback: callable | None = None,
    ) -> dict[str, Any]:
        """
        Press a key or key combination

        Args:
            key: Key to press (e.g., 'enter', 'ctrl', 'a')
            presses: Number of times to press
            interval: Interval between presses
            approval_callback: Approval callback

        Returns:
            Dictionary with operation result
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            pyautogui.press(params["key"], presses=params["presses"], interval=params["interval"])
            return {"key": params["key"], "presses": params["presses"]}

        return await self.execute_operation(
            operation_type="keyboard_type",
            description=f"Press key: {key}",
            parameters={"key": key, "presses": presses, "interval": interval},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def hotkey(self, *keys: str, approval_callback: callable | None = None) -> dict[str, Any]:
        """
        Press a key combination (hotkey)

        Args:
            *keys: Keys to press together (e.g., 'ctrl', 'c')
            approval_callback: Approval callback

        Returns:
            Dictionary with operation result
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            pyautogui.hotkey(*params["keys"])
            return {"hotkey": "+".join(params["keys"])}

        return await self.execute_operation(
            operation_type="keyboard_type",
            description=f"Press hotkey: {'+'.join(keys)}",
            parameters={"keys": list(keys)},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def click(
        self,
        x: int | None = None,
        y: int | None = None,
        clicks: int = 1,
        interval: float = 0.0,
        button: str = "left",
        approval_callback: callable | None = None,
    ) -> dict[str, Any]:
        """
        Click mouse at position

        Args:
            x: X coordinate (None for current position)
            y: Y coordinate (None for current position)
            clicks: Number of clicks
            interval: Interval between clicks
            button: Mouse button ('left', 'right', 'middle')
            approval_callback: Approval callback

        Returns:
            Dictionary with operation result
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            pyautogui.click(
                x=params["x"],
                y=params["y"],
                clicks=params["clicks"],
                interval=params["interval"],
                button=params["button"],
            )
            return {
                "x": params["x"],
                "y": params["y"],
                "clicks": params["clicks"],
                "button": params["button"],
            }

        return await self.execute_operation(
            operation_type="mouse_click",
            description=f"Click at ({x}, {y})",
            parameters={"x": x, "y": y, "clicks": clicks, "interval": interval, "button": button},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def move_mouse(
        self, x: int, y: int, duration: float = 0.0, approval_callback: callable | None = None
    ) -> dict[str, Any]:
        """
        Move mouse to position

        Args:
            x: X coordinate
            y: Y coordinate
            duration: Duration of movement (seconds)
            approval_callback: Approval callback

        Returns:
            Dictionary with operation result
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            pyautogui.moveTo(params["x"], params["y"], duration=params["duration"])
            return {"x": params["x"], "y": params["y"]}

        return await self.execute_operation(
            operation_type="mouse_move",
            description=f"Move mouse to ({x}, {y})",
            parameters={"x": x, "y": y, "duration": duration},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def drag_mouse(
        self,
        x: int,
        y: int,
        duration: float = 0.0,
        button: str = "left",
        approval_callback: callable | None = None,
    ) -> dict[str, Any]:
        """
        Drag mouse to position

        Args:
            x: X coordinate
            y: Y coordinate
            duration: Duration of drag (seconds)
            button: Mouse button to hold
            approval_callback: Approval callback

        Returns:
            Dictionary with operation result
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            pyautogui.drag(
                params["x"], params["y"], duration=params["duration"], button=params["button"]
            )
            return {"x": params["x"], "y": params["y"], "button": params["button"]}

        return await self.execute_operation(
            operation_type="mouse_click",
            description=f"Drag mouse to ({x}, {y})",
            parameters={"x": x, "y": y, "duration": duration, "button": button},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def scroll(
        self,
        clicks: int,
        x: int | None = None,
        y: int | None = None,
        approval_callback: callable | None = None,
    ) -> dict[str, Any]:
        """
        Scroll mouse wheel

        Args:
            clicks: Number of clicks (positive=up, negative=down)
            x: X coordinate (None for current position)
            y: Y coordinate (None for current position)
            approval_callback: Approval callback

        Returns:
            Dictionary with operation result
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            pyautogui.scroll(params["clicks"], x=params["x"], y=params["y"])
            return {
                "clicks": params["clicks"],
                "direction": "up" if params["clicks"] > 0 else "down",
            }

        return await self.execute_operation(
            operation_type="mouse_click",
            description=f"Scroll {abs(clicks)} clicks {'up' if clicks > 0 else 'down'}",
            parameters={"clicks": clicks, "x": x, "y": y},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def get_mouse_position(self, approval_callback: callable | None = None) -> dict[str, Any]:
        """
        Get current mouse position

        Args:
            approval_callback: Approval callback

        Returns:
            Dictionary with mouse position
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            x, y = pyautogui.position()
            return {"x": x, "y": y}

        return await self.execute_operation(
            operation_type="mouse_move",
            description="Get mouse position",
            parameters={},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def get_screen_size(self, approval_callback: callable | None = None) -> dict[str, Any]:
        """
        Get screen size

        Args:
            approval_callback: Approval callback

        Returns:
            Dictionary with screen dimensions
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            width, height = pyautogui.size()
            return {"width": width, "height": height}

        return await self.execute_operation(
            operation_type="system_info",
            description="Get screen size",
            parameters={},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def locate_on_screen(
        self, image_path: str, confidence: float = 0.9, approval_callback: callable | None = None
    ) -> dict[str, Any]:
        """
        Locate an image on screen

        Args:
            image_path: Path to image to find
            confidence: Confidence threshold (0.0-1.0)
            approval_callback: Approval callback

        Returns:
            Dictionary with image location
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            try:
                location = pyautogui.locateOnScreen(
                    params["image_path"], confidence=params["confidence"]
                )
                if location:
                    return {
                        "found": True,
                        "left": location.left,
                        "top": location.top,
                        "width": location.width,
                        "height": location.height,
                        "center_x": location.left + location.width // 2,
                        "center_y": location.top + location.height // 2,
                    }
                else:
                    return {"found": False}
            except Exception as e:
                return {"found": False, "error": str(e)}

        return await self.execute_operation(
            operation_type="system_info",
            description=f"Locate image on screen: {image_path}",
            parameters={"image_path": image_path, "confidence": confidence},
            executor=executor,
            approval_callback=approval_callback,
        )


# Global instance
_desktop_automation = None


def get_desktop_automation() -> DesktopAutomation:
    """Get the global desktop automation instance"""
    global _desktop_automation
    if _desktop_automation is None:
        _desktop_automation = DesktopAutomation()
    return _desktop_automation
