import React, { useState, useEffect } from 'react';
import { Form, InputNumber, Button, Card, Typography, Row, Col, Divider, Select, Alert } from 'antd';
import { DollarOutlined, SolutionOutlined, UserOutlined, ClockCircleOutlined, HomeOutlined, TeamOutlined, SafetyCertificateOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

const CreditForm = ({ onSubmit, isLoading }) => {
  const [form] = Form.useForm();
  const [loanTerm, setLoanTerm] = useState(null); 

  // Hàm tự động tính toán thời gian vay khi nhập tiền
  const calculateTerm = (_, allValues) => {
    const { AMT_CREDIT, AMT_ANNUITY } = allValues;
    if (AMT_CREDIT && AMT_ANNUITY && AMT_ANNUITY > 0) {
      const months = AMT_CREDIT / AMT_ANNUITY;
      const years = months / 12;
      setLoanTerm(years);
    } else {
      setLoanTerm(null);
    }
  };

  const onFinish = (values) => {
    const formattedValues = {
      ...values,
      DAYS_BIRTH: -Math.abs(values.age * 365), 
      DAYS_EMPLOYED: -Math.abs(values.years_employed * 365),
    };
    onSubmit(formattedValues);
  };

  return (
    <Card 
      style={{ height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 12, border: 'none', boxShadow: 'none' }}
      bodyStyle={{ flex: 1, padding: '0 10px' }}
    >
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0, color: '#1f1f1f' }}>Hồ sơ vay vốn</Title>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        onValuesChange={calculateTerm} 
        size="large"
        initialValues={{
          AMT_INCOME_TOTAL: 50000000, 
          AMT_CREDIT: 1000000000,
          AMT_ANNUITY: 25000000,
          age: 30,
          years_employed: 5,
          NAME_HOUSING_TYPE: "House / apartment",
          NAME_FAMILY_STATUS: "Married",
          EXT_SOURCE_2: 0.85
        }}
      >
        <Title level={5} style={{ color: '#B01E23' }}><DollarOutlined /> Tài chính</Title>
        
        {/* CẢNH BÁO NẾU THỜI GIAN VAY QUÁ VÔ LÝ */}
        {loanTerm && loanTerm > 30 && (
          <Alert 
            message="Cảnh báo nhập liệu" 
            description={`Với số tiền trả hàng tháng này, bạn cần ${loanTerm.toFixed(1)} năm mới trả hết nợ. Vui lòng tăng số tiền trả hàng tháng.`} 
            type="error" 
            showIcon 
            style={{ marginBottom: 15 }}
          />
        )}

        <Row gutter={16}>
          <Col span={24}>
            <Form.Item label="Tổng thu nhập (năm)" name="AMT_INCOME_TOTAL" rules={[{ required: true }]}>
               <InputNumber 
                 style={{ width: '100%' }} 
                 min={10000000} // Min 10 tr
                 formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} 
                 parser={value => value.replace(/\$\s?|(,*)/g, '')} 
                 addonAfter="VND" 
               />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="Số tiền muốn vay" name="AMT_CREDIT" rules={[{ required: true }]}>
               <InputNumber 
                 style={{ width: '100%' }} 
                 min={10000000} 
                 formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} 
                 parser={value => value.replace(/\$\s?|(,*)/g, '')} 
               />
            </Form.Item>
          </Col>
          <Col span={12}>
             <Form.Item label="Khả năng trả/tháng" name="AMT_ANNUITY" rules={[{ required: true }]}>
               <InputNumber 
                 style={{ width: '100%' }} 
                 min={500000} // Bắt buộc nhập tối thiểu 500k
                 formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} 
                 parser={value => value.replace(/\$\s?|(,*)/g, '')} 
               />
            </Form.Item>
          </Col>
        </Row>

        <Divider style={{ margin: '12px 0' }} />

        <Title level={5} style={{ color: '#B01E23' }}><SolutionOutlined /> Nhân khẩu & Hành vi</Title>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="Tuổi" name="age" rules={[{ required: true }]}>
              <InputNumber style={{ width: '100%' }} min={18} max={70} prefix={<UserOutlined />} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="Thâm niên (năm)" name="years_employed">
              <InputNumber style={{ width: '100%' }} min={0} max={40} prefix={<ClockCircleOutlined />} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="Nhà ở" name="NAME_HOUSING_TYPE">
              <Select>
                <Option value="House / apartment">Nhà riêng</Option>
                <Option value="Rented apartment">Nhà thuê</Option>
                <Option value="With parents">Ở cùng bố mẹ</Option>
                <Option value="Municipal apartment">Nhà ở xã hội</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="Gia đình" name="NAME_FAMILY_STATUS">
              <Select>
                 <Option value="Married">Đã kết hôn</Option>
                 <Option value="Single / not married">Độc thân</Option>
                 <Option value="Civil marriage">Sống chung</Option>
                 <Option value="Separated">Ly thân / Ly dị</Option>
              </Select>
            </Form.Item>
          </Col>
          
          <Col span={24}>
             <Form.Item 
                label={<span style={{color: '#B01E23', fontWeight: 'bold'}}>Lịch sử Tín dụng</span>} 
                name="EXT_SOURCE_2"
             >
               <Select size="large" style={{ border: '1px solid #B01E23', borderRadius: 6 }}>
                 <Option value={0.85}>Rất Tốt (Chưa từng trễ hạn)</Option>
                 <Option value={0.65}>Khá (Thỉnh thoảng trễ nhẹ)</Option>
                 <Option value={0.35}>Trung bình (Có nợ chú ý)</Option>
                 {/* Value thấp (0.1) để kích hoạt AI reject */}
                 <Option value={0.10}>Nợ Xấu (Đang có nợ quá hạn)</Option>
               </Select>
             </Form.Item>
          </Col>
        </Row>

        <Form.Item style={{ marginTop: 20 }}>
          <Button 
            type="primary" htmlType="submit" size="large" block loading={isLoading}
            style={{ height: 50, fontSize: 18, fontWeight: 700, background: '#B01E23', borderColor: '#B01E23' }}
          >
            PHÂN TÍCH HỒ SƠ
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default CreditForm;