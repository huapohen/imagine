# LB1 串口协议

唯一现行规范位于 [docs/software/serial-protocol.md](../docs/software/serial-protocol.md)，共用 [golden vectors](../docs/software/serial-golden-vectors.tsv)。旧 LBP NDJSON 草案不再支持；没有 ttl_ms 或 TOUCH/PRIVACY 推送类型。

```sh
./firmware/test.sh
./software/test-integration.sh
```

LB1 ASCII + CRC16，115200 8N1，最大 256 bytes，16 项 FIFO 重试缓存，GET/PING 心跳 5 秒失效安全离线。精确字段、UTF-8 hex 验证、错误优先级、物理隐私时序均见唯一规范。
