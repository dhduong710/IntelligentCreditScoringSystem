import React from 'react';
import { Result, Tag, Typography, Statistic, Row, Col, Progress, Alert } from 'antd';
import { Gauge } from '@ant-design/plots';
import { CheckCircleFilled, CloseCircleFilled, InfoCircleOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;

const ResultCard = ({ data }) => {
  if (!data) return null;

  const isApproved = data.status === "APPROVE";
  const scoreColor = isApproved ? '#52c41a' : '#f5222d'; 
  
  // Cấu hình Gauge Chart
  const config = {
    percent: data.probability,
    range: {
      color: 'l(0) 0:#52c41a 0.5:#faad14 1:#f5222d', 
    },
    indicator: {
      pointer: { style: { stroke: '#D0D0D0' } },
      pin: { style: { stroke: '#D0D0D0' } },
    },
    statistic: {
      content: {
        style: { fontSize: '36px', lineHeight: '36px', color: '#4B535E', fontWeight: 'bold' },
        formatter: () => `${(data.probability * 100).toFixed(1)}%`,
      },
    },
    gaugeStyle: {
        lineCap: 'round',
    },
  };

  return (
    <div style={{ padding: '0 20px', textAlign: 'center' }}>
      <Tag color={isApproved ? "success" : "error"} style={{ padding: '5px 15px', fontSize: 14, marginBottom: 20 }}>
         {isApproved ? "HỒ SƠ RỦI RO THẤP" : "HỒ SƠ RỦI RO CAO"}
      </Tag>

      <Title level={2} style={{ color: scoreColor, margin: '10px 0' }}>
         {isApproved ? <CheckCircleFilled /> : <CloseCircleFilled />} {isApproved ? "HỒ SƠ ĐƯỢC DUYỆT" : "TỪ CHỐI KHOẢN VAY"}
      </Title>
      
      <Text style={{ fontSize: 16 }}>
        {data.message}
      </Text>

      <Row justify="center" align="middle" style={{ marginTop: 40, marginBottom: 20 }}>
         <Col span={24} style={{ height: 220 }}>
             <Gauge {...config} />
         </Col>
      </Row>

      <div style={{ background: '#f9f9f9', padding: 20, borderRadius: 8, marginTop: 20 }}>
        <Row gutter={16}>
            <Col span={12}>
                <Statistic title="Điểm Tín dụng" value={data.credit_score} valueStyle={{ color: scoreColor, fontWeight: 'bold' }} />
            </Col>
            <Col span={12}>
                <Statistic title="Ngưỡng rủi ro hệ thống" value={`${(data.threshold * 100).toFixed(1)}%`} />
            </Col>
        </Row>
      </div>
      
      {!isApproved && (
          <Alert 
            message="Khuyến nghị"
            description="Khách hàng này có rủi ro cao dựa trên thu nhập và lịch sử tín dụng giả lập. Cần thẩm định thủ công kỹ hơn trước khi duyệt."
            type="warning"
            showIcon
            style={{ marginTop: 20, textAlign: 'left' }}
          />
      )}
    </div>
  );
};

export default ResultCard;