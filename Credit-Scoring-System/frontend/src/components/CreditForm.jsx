import React from 'react';
import { Form, InputNumber, Button, Card, Typography, Row, Col, Divider, Select } from 'antd';
import { DollarOutlined, SolutionOutlined, UserOutlined, ClockCircleOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

const CreditForm = ({ onSubmit, isLoading }) => {
  const [form] = Form.useForm();

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
      style={{ height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 12 }}
      bodyStyle={{ flex: 1, padding: '32px 24px' }}
      hoverable
    >
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>Hồ sơ vay vốn</Title>
        <Text type="secondary">Nhập thông tin khách hàng để hệ thống chấm điểm.</Text>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        size="large"
        initialValues={{
          AMT_INCOME_TOTAL: 50000000,
          AMT_CREDIT: 1000000000,
          AMT_ANNUITY: 25000000,
          age: 30,
          years_employed: 5,
          gender: 'M',
          education: 'University'
        }}
      >
        <Title level={5} style={{ color: '#B01E23', marginTop: 0 }}><DollarOutlined /> Thông tin Tài chính</Title>
        <Row gutter={16}>
          <Col span={24}>
            <Form.Item label="Tổng thu nhập hàng năm (VND)" name="AMT_INCOME_TOTAL" rules={[{ required: true }]}>
              <InputNumber 
                style={{ width: '100%' }} 
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
                formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={value => value.replace(/\$\s?|(,*)/g, '')}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="Khả năng trả/tháng" name="AMT_ANNUITY" rules={[{ required: true }]}>
              <InputNumber 
                style={{ width: '100%' }}
                formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={value => value.replace(/\$\s?|(,*)/g, '')}
              />
            </Form.Item>
          </Col>
        </Row>

        <Divider style={{ margin: '12px 0 24px 0' }} />

        <Title level={5} style={{ color: '#B01E23' }}><SolutionOutlined /> Thông tin Cá nhân</Title>
        <Row gutter={16}>
          <Col span={12}>
             <Form.Item label="Giới tính" name="gender">
                <Select>
                    <Option value="M">Nam</Option>
                    <Option value="F">Nữ</Option>
                </Select>
             </Form.Item>
          </Col>
          <Col span={12}>
             <Form.Item label="Trình độ học vấn" name="education">
                <Select>
                    <Option value="Secondary">Trung học</Option>
                    <Option value="University">Đại học / Cao đẳng</Option>
                </Select>
             </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="Tuổi" name="age" rules={[{ required: true }]}>
              <InputNumber style={{ width: '100%' }} min={18} max={70} prefix={<UserOutlined />} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="Thâm niên (năm)" name="years_employed" rules={[{ required: true }]}>
              <InputNumber style={{ width: '100%' }} min={0} max={50} prefix={<ClockCircleOutlined />} />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item style={{ marginTop: 32 }}>
          <Button 
            type="primary" 
            htmlType="submit" 
            size="large" 
            block 
            loading={isLoading}
            style={{ height: 50, fontSize: 18, fontWeight: 600, boxShadow: '0 4px 15px rgba(176, 30, 35, 0.4)' }}
          >
            PHÂN TÍCH HỒ SƠ
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default CreditForm;