package com.yuxiaotu.trade.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yuxiaotu.trade.dto.response.OrderVO;
import com.yuxiaotu.trade.entity.OrderEntity;
import com.yuxiaotu.trade.entity.OrderItemEntity;
import com.yuxiaotu.trade.mapper.OrderItemMapper;
import org.springframework.stereotype.Component;

import java.time.ZoneId;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Component
public class OrderViewHelper {
    private static final ZoneId BEIJING = ZoneId.of("Asia/Shanghai");
    private static final DateTimeFormatter BEIJING_FMT =
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private static final Map<String, String> STATUS_LABELS = Map.of(
            "pending_payment", "待支付",
            "paid", "待发货",
            "shipped", "运输中",
            "completed", "已完成",
            "cancelled", "已取消"
    );

    private final OrderItemMapper orderItemMapper;

    public OrderViewHelper(OrderItemMapper orderItemMapper) {
        this.orderItemMapper = orderItemMapper;
    }

    public OrderVO toVo(OrderEntity order) {
        List<OrderItemEntity> items = orderItemMapper.selectList(
                new LambdaQueryWrapper<OrderItemEntity>().eq(OrderItemEntity::getOrderId, order.getId())
        );
        OrderVO vo = new OrderVO();
        vo.setId(order.getId());
        vo.setOrderNo(order.getOrderNo());
        vo.setTotalAmount(order.getTotalAmount().doubleValue());
        vo.setStatus(order.getStatus());
        vo.setStatusLabel(STATUS_LABELS.getOrDefault(order.getStatus(), order.getStatus()));
        vo.setReceiverName(order.getReceiverName());
        vo.setReceiverPhone(order.getReceiverPhone());
        vo.setReceiverAddress(order.getReceiverAddress());
        vo.setPayTime(format(order.getPayTime()));
        vo.setCreatedAt(format(order.getCreatedAt()));
        vo.setShipCompany(order.getShipCompany());
        vo.setShipTrackingNo(order.getShipTrackingNo());
        vo.setShippedAt(format(order.getShippedAt()));
        vo.setCompletedAt(format(order.getCompletedAt()));
        vo.setItems(items.stream().map(item -> {
            Map<String, Object> map = new HashMap<>();
            map.put("book_id", item.getBookId());
            map.put("book_title", item.getBookTitle());
            map.put("price", item.getPrice().doubleValue());
            map.put("quantity", item.getQuantity());
            return map;
        }).collect(Collectors.toList()));
        return vo;
    }

    /** DB 存 UTC naive，输出北京时间字符串 */
    private String format(java.time.LocalDateTime time) {
        if (time == null) {
            return null;
        }
        return time.atZone(ZoneOffset.UTC)
                .withZoneSameInstant(BEIJING)
                .format(BEIJING_FMT);
    }
}
