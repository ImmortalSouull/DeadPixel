set(TARGET T2Passthrough)

add_library(${TARGET} SHARED
    dllmain.cpp
    compositor.cpp
    crash_guard.cpp
    ws.cpp
)

target_include_directories(${TARGET} PRIVATE . "${RESHADE_INCLUDE}")
target_compile_definitions(${TARGET} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
target_link_libraries(${TARGET} PUBLIC UE4SS)
target_link_libraries(${TARGET} PRIVATE ws2_32 d3d11)
