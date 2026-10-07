// Calling a UFunction through ProcessEvent with its parameters laid out by reflection (offsets from the function's
// own properties), so no engine headers or hard-coded layouts are needed. Game thread only.
#pragma once
#include <cstdint>
#include <cstring>
#include <string>
#include <algorithm>
#include <type_traits>

#include <DynamicOutput/DynamicOutput.hpp>
#include <Unreal/CoreUObject/UObject/Class.hpp>
#include <Unreal/CoreUObject/UObject/UnrealType.hpp>
#include <Unreal/UFunction.hpp>
#include <Unreal/UObject.hpp>
#include <Unreal/UObjectGlobals.hpp>

namespace ue
{
	/// FVector as UE 4.27 lays it out (floats); built from doubles, the mod's own maths stays in double.
	struct Vec
	{
		float x = 0, y = 0, z = 0;
		Vec() = default;
		Vec(double ax, double ay, double az) : x(float(ax)), y(float(ay)), z(float(az)) {}
	};
	static_assert(sizeof(Vec) == 12);

	/// FRotator (UE 4.27, floats): pitch, yaw, roll in degrees.
	struct Rot
	{
		float pitch = 0, yaw = 0, roll = 0;
		Rot() = default;
		Rot(double p, double y, double r) : pitch(float(p)), yaw(float(y)), roll(float(r)) {}
	};
	static_assert(sizeof(Rot) == 12);

	/// FTransform (UE 4.27, floats): rotation quaternion, translation, scale, each 16-byte aligned (16 bytes apiece).
	struct alignas(16) Transform
	{
		float qx = 0, qy = 0, qz = 0, qw = 1;
		float tx = 0, ty = 0, tz = 0, pad0 = 0;
		float sx = 1, sy = 1, sz = 1, pad1 = 0;
	};
	static_assert(sizeof(Transform) == 48);

	/// TArray<T*> as UE lays it out (the data is ours: only pass it to parameters the callee doesn't resize).
	struct PtrArray
	{
		RC::Unreal::UObject **data;
		int32_t num, max;
	};

	inline RC::Unreal::UObject *find(const TCHAR *path)
	{
		return RC::Unreal::UObjectGlobals::StaticFindObject<RC::Unreal::UObject *>(nullptr, nullptr, path);
	}

	class Call
	{
	public:
		/// fn: "/Script/Module.Class:Function". The target defaults to the class's default object (static functions).
		explicit Call(const TCHAR *fn)
		{
			m_fn = RC::Unreal::UObjectGlobals::StaticFindObject<RC::Unreal::UFunction *>(nullptr, nullptr, fn);
			if (m_fn == nullptr)
			{
				RC::Output::send<RC::LogLevel::Warning>(STR("[T2Passthrough] no UFunction {}\n"), fn);
				return;
			}
			m_size = m_fn->GetParmsSize();
			if (m_size > int32_t(sizeof(m_params)))
			{
				RC::Output::send<RC::LogLevel::Warning>(STR("[T2Passthrough] {}: {} bytes of parameters\n"), fn, m_size);
				m_fn = nullptr;
				return;
			}
			std::memset(m_params, 0, sizeof(m_params));
		}

		bool ok() const
		{
			return m_fn != nullptr;
		}

		template <typename T>
		Call &set(const TCHAR *name, const T &value)
		{
			if (RC::Unreal::FProperty *p = prop(name))
			{
				auto *b = RC::Unreal::CastField<RC::Unreal::FBoolProperty>(p);
				if constexpr (std::is_arithmetic_v<T>)
				{
					// numbers go in as the parameter's own type (a double literal into a float parameter wrote 8 bytes)
					uint8_t *at = m_params + p->GetOffset_Internal();
					if (b != nullptr)
						b->SetPropertyValueInContainer(m_params, bool(value));
					else if (RC::Unreal::CastField<RC::Unreal::FFloatProperty>(p))
						*reinterpret_cast<float *>(at) = float(value);
					else if (RC::Unreal::CastField<RC::Unreal::FDoubleProperty>(p))
						*reinterpret_cast<double *>(at) = double(value);
					else if (RC::Unreal::CastField<RC::Unreal::FIntProperty>(p))
						*reinterpret_cast<int32_t *>(at) = int32_t(value);
					else if (p->GetSize() == 1)
						*at = uint8_t(value);
					else
						std::memcpy(at, &value, std::min<size_t>(sizeof(T), size_t(p->GetSize())));
					return *this;
				}
				std::memcpy(m_params + p->GetOffset_Internal(), &value, std::min<size_t>(sizeof(T), size_t(p->GetSize())));
			}
			return *this;
		}

		/// Raw bytes into a parameter (a struct copied from another call's result), at most the parameter's size.
		Call &raw(const TCHAR *name, const void *data, size_t size)
		{
			if (RC::Unreal::FProperty *p = prop(name))
				std::memcpy(m_params + p->GetOffset_Internal(), data, std::min<size_t>(size, size_t(p->GetSize())));
			return *this;
		}

		/// A parameter's bytes after the call (an out struct, e.g. an FHitResult) and its size.
		const uint8_t *bytes(const TCHAR *name, int32_t &size)
		{
			RC::Unreal::FProperty *p = prop(name);
			size = p ? p->GetSize() : 0;
			return p ? m_params + p->GetOffset_Internal() : nullptr;
		}

		Call &name(const TCHAR *param, const TCHAR *value)
		{
			const RC::Unreal::FName n(value, RC::Unreal::FNAME_Add);
			return set(param, n);
		}

		template <typename T>
		T get(const TCHAR *name)
		{
			T value{};
			if (RC::Unreal::FProperty *p = prop(name))
			{
				auto *b = RC::Unreal::CastField<RC::Unreal::FBoolProperty>(p);
				if constexpr (std::is_arithmetic_v<T>)
				{
					if (b != nullptr)
						return T(b->GetPropertyValueInContainer(m_params));
				}
				std::memcpy(&value, m_params + p->GetOffset_Internal(), sizeof(T));
			}
			return value;
		}

		/// Calls it on target (or on the function's class default object when target is null).
		bool run(RC::Unreal::UObject *target = nullptr)
		{
			if (m_fn == nullptr)
				return false;
			if (target == nullptr)
			{
				if (m_cdo == nullptr)
					m_cdo = static_cast<RC::Unreal::UClass *>(m_fn->GetOuterPrivate())->GetClassDefaultObject().Get();
				target = m_cdo;
			}
			if (target == nullptr)
				return false;
			target->ProcessEvent(m_fn, m_params);
			return true;
		}

	private:
		RC::Unreal::FProperty *prop(const TCHAR *name)
		{
			if (m_fn == nullptr)
				return nullptr;
			RC::Unreal::FProperty *p = m_fn->FindProperty(RC::Unreal::FName(name, RC::Unreal::FNAME_Find));
			if (p == nullptr)
				RC::Output::send<RC::LogLevel::Warning>(STR("[T2Passthrough] no parameter {}\n"), name);
			return p;
		}

		RC::Unreal::UFunction *m_fn = nullptr;
		RC::Unreal::UObject *m_cdo = nullptr;
		int32_t m_size = 0;
		alignas(16) uint8_t m_params[1024];
	};
}
