from typing import Generic, TypeVar, Union, Callable, Any
from dataclasses import dataclass
from functools import wraps

T = TypeVar('T')
E = TypeVar('E')


@dataclass
class Success(Generic[T]):
    """Representa un resultado exitoso"""
    value: T
    
    def is_success(self) -> bool:
        return True
    
    def is_failure(self) -> bool:
        return False
    
    def unwrap(self) -> T:
        """Obtiene el valor del resultado exitoso"""
        return self.value
    
    def map(self, func: Callable[[T], Any]) -> 'Result':
        """Aplica una función al valor si es exitoso"""
        try:
            return Success(func(self.value))
        except Exception as e:
            return Failure(e)


@dataclass
class Failure(Generic[E]):
    """Representa un resultado fallido"""
    error: E
    
    def is_success(self) -> bool:
        return False
    
    def is_failure(self) -> bool:
        return True
    
    def unwrap(self) -> None:
        """Lanza el error del resultado fallido"""
        if isinstance(self.error, Exception):
            raise self.error
        raise Exception(f"Result failed with error: {self.error}")
    
    def map(self, func: Callable[[Any], Any]) -> 'Result':
        """No aplica función si es fallido"""
        return self


Result = Union[Success[T], Failure[E]]


class ResultBuilder:
    """Builder para crear resultados"""
    
    @staticmethod
    def success(value: T) -> Success[T]:
        return Success(value)
    
    @staticmethod
    def failure(error: E) -> Failure[E]:
        return Failure(error)
    
    @staticmethod
    def from_callable(func: Callable[[], T]) -> Result[T, Exception]:
        """Ejecuta una función y captura excepciones como Result"""
        try:
            return Success(func())
        except Exception as e:
            return Failure(e)


def result_handler(func):
    """Decorador que convierte excepciones en Results"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return ResultBuilder.success(result)
        except Exception as e:
            return ResultBuilder.failure(e)
    return wrapper
