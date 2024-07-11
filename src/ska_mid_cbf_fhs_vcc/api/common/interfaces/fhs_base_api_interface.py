from abc import ABC, abstractmethod


class FhsBaseApiInterface(ABC):

    @classmethod
    def __subclasshook__(cls, subclass: type) -> bool:
        return (
            hasattr(subclass, 'recover')
            and callable(subclass.recover)
            and hasattr(subclass, 'configure')
            and callable(subclass.configure)
            and hasattr(subclass, 'start')
            and callable(subclass.start)
            and hasattr(subclass, 'stop')
            and callable(subclass.stop)
            and hasattr(subclass, 'deconfigure')
            and callable(subclass.deconfigure)
            and hasattr(subclass, 'status')
            and callable(subclass.status)
            or NotImplemented
        )

    @abstractmethod
    def recover(self) -> None:
        raise NotImplementedError('Method is abstract')
    
    @abstractmethod
    def configure(self, config) -> None:
        raise NotImplementedError('Method is abstract')

    @abstractmethod
    def start(self) -> int:
        raise NotImplementedError('Method is abstract')

    @abstractmethod
    def stop(self, force: bool = False) -> int:
        raise NotImplementedError('Method is abstract')

    @abstractmethod
    def deconfigure(self, config) -> None:
        raise NotImplementedError('Method is abstract')

    @abstractmethod
    def status(self, status, clear: bool = False) -> str:
        raise NotImplementedError('Method is abstract')
